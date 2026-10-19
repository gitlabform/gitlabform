import sys
from logging import critical, info
from typing import Dict, List

from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Project, ProjectApprovalRule

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class MergeRequestsApprovalRules(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("merge_requests_approval_rules", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        # copy, so that popping "enforce" does not mutate the shared configuration,
        # which is reused when this method is retried
        configured_rules: Dict = dict(configuration.get("merge_requests_approval_rules", {}))
        enforce = configured_rules.pop("enforce", False)

        # Rules are matched against GitLab by name, so entries sharing a name would
        # reconcile ambiguously; reject them before any changes are made.
        self._fail_on_duplicate_names(project_and_group, configured_rules)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_rules: List[ProjectApprovalRule] = project.approvalrules.list(get_all=True)

        # Resolve branch names to ids before anything is deleted, so that a bad branch
        # name in the config fails the section before it can remove existing rules,
        # and so that each unique branch is fetched only once.
        protected_branch_ids = self._protected_branch_ids(project, configured_rules)

        if enforce:
            # Delete stale rules before adding new ones, so that unique-constraint slots
            # (e.g. only one any_approver rule per project) are freed for the rules below.
            configured_names = {c.get("name") for c in configured_rules.values() if c.get("name")}
            for existing in existing_rules:
                if existing.name not in configured_names:
                    info(
                        f"Deleting rule '{existing.name}' of {self.configuration_name} in {project_and_group}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()
            existing_rules = [rule for rule in existing_rules if rule.name in configured_names]

        for entity_name, rule_config in configured_rules.items():
            name = rule_config.get("name")
            matching = next((rule for rule in existing_rules if rule.name == name), None)

            if rule_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of {self.configuration_name} in {project_and_group}")
                    matching.delete()
                else:
                    info(
                        f"Not deleting {entity_name} of {self.configuration_name} in {project_and_group},"
                        f" because it doesn't exist"
                    )
                continue

            if matching:
                if self._needs_update(matching.asdict(), rule_config):
                    info(f" * Editing {entity_name} of {self.configuration_name} in {project_and_group}")
                    project.approvalrules.update(
                        matching.id, self._payload_for_update(rule_config, protected_branch_ids)
                    )
                else:
                    info(
                        f" * {entity_name} of {self.configuration_name} in {project_and_group}"
                        f" doesn't need an update."
                    )
            else:
                info(f" * Adding {entity_name} of {self.configuration_name} in {project_and_group}")
                project.approvalrules.create(self._payload_for_create(rule_config, protected_branch_ids))

    def _needs_update(self, entity_in_gitlab: Dict, entity_in_configuration: Dict) -> bool:
        # GitLab returns users/groups as lists of objects and protected_branches as list
        # of objects with a "name" field, while the config (post-transform) has user_ids /
        # group_ids as int lists and protected_branches as list of names. Without
        # normalization the base _needs_update always triggers an update, even when nothing
        # changed. We normalize both sides unconditionally so keys line up regardless of
        # whether GitLab omitted an empty list or the user omitted the field in config.
        gitlab_norm = dict(entity_in_gitlab)
        gitlab_norm["user_ids"] = sorted(u["id"] for u in gitlab_norm.pop("users", []))
        gitlab_norm["group_ids"] = sorted(g["id"] for g in gitlab_norm.pop("groups", []))
        gitlab_protected_branches = gitlab_norm.pop("protected_branches", [])

        # The update payload still sends omitted user_ids/group_ids/protected_branches as
        # empty lists (old behavior, kept until #1468), so the comparison here has to
        # mirror what _payload_for_update will send, or a rule would never converge.
        # "delete" is a gitlabform control key, not a rule attribute.
        config_norm = dict(entity_in_configuration)
        config_norm.pop("delete", None)
        config_norm["user_ids"] = sorted(config_norm.get("user_ids", []))
        config_norm["group_ids"] = sorted(config_norm.get("group_ids", []))

        # The config can reference branches by name (protected_branches) or directly
        # by id (protected_branch_ids); compare whichever representation it uses.
        if "protected_branch_ids" in config_norm:
            gitlab_norm["protected_branch_ids"] = sorted(b["id"] for b in gitlab_protected_branches)
            config_norm["protected_branch_ids"] = sorted(config_norm["protected_branch_ids"])
        if "protected_branch_ids" not in config_norm or "protected_branches" in config_norm:
            gitlab_norm["protected_branches"] = sorted(b["name"] for b in gitlab_protected_branches)
            config_norm["protected_branches"] = sorted(config_norm.get("protected_branches", []))

        return super()._needs_update(gitlab_norm, config_norm)

    def _fail_on_duplicate_names(self, project_and_group: str, configured_rules: Dict) -> None:
        names = [rule_config.get("name") for rule_config in configured_rules.values() if rule_config.get("name")]
        duplicates = {name for name in names if names.count(name) > 1}
        if duplicates:
            critical(
                f"Entities in {self.configuration_name} for {project_and_group}"
                f" share the same name(s): {sorted(duplicates)}"
            )
            sys.exit(EXIT_INVALID_INPUT)

    @staticmethod
    def _protected_branch_ids(project: Project, configured_rules: Dict) -> Dict[str, int]:
        branch_names = {
            branch_name
            for rule_config in configured_rules.values()
            if not rule_config.get("delete", False)
            for branch_name in rule_config.get("protected_branches", [])
        }
        if not branch_names:
            return {}

        existing = {branch.name: branch.id for branch in project.protectedbranches.list(get_all=True)}
        missing = branch_names - existing.keys()
        if missing:
            raise GitlabGetError(
                f"Protected branches {sorted(missing)} not found in this project",
                response_code=404,
            )
        return {branch_name: existing[branch_name] for branch_name in branch_names}

    @staticmethod
    def _payload_for_create(rule_config: Dict, protected_branch_ids: Dict[str, int]) -> Dict:
        # "delete" is a gitlabform control key and should not be sent to the API
        payload = {k: v for k, v in rule_config.items() if k != "delete"}
        if "protected_branches" in payload:
            # the API expects protected_branch_ids, while the config has branch names
            branch_names = payload.pop("protected_branches")
            payload["protected_branch_ids"] = [protected_branch_ids[branch_name] for branch_name in branch_names]
        return payload

    def _payload_for_update(self, rule_config: Dict, protected_branch_ids: Dict[str, int]) -> Dict:
        payload = self._payload_for_create(rule_config, protected_branch_ids)
        # GitLab interprets omitted user_ids/group_ids/protected_branch_ids as "no change",
        # but the old code sent them as empty lists, clearing them. That behavior is kept
        # for now; changing it is a breaking change, tracked in #1468.
        payload.setdefault("user_ids", [])
        payload.setdefault("group_ids", [])
        payload.setdefault("protected_branch_ids", [])
        return payload
