import sys
from logging import critical, info
from typing import Dict, List

from gitlab.v4.objects import Project, ProjectApprovalRule

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class MergeRequestsApprovalRules(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("merge_requests_approval_rules", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_rules: Dict = configuration.get("merge_requests_approval_rules", {})
        enforce = configured_rules.pop("enforce", False)

        self._find_duplicates(project_and_group, configured_rules)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_rules: List[ProjectApprovalRule] = list(project.approvalrules.list(get_all=True))

        handled_names: set = set()

        for entity_name, rule_config in configured_rules.items():
            name = rule_config.get("name")
            if not name:
                critical(
                    f"Entity {entity_name} in merge_requests_approval_rules for {project_and_group}"
                    f" doesn't have its defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)

            matching = next((r for r in existing_rules if r.name == name), None)

            if rule_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of merge_requests_approval_rules in {project_and_group}")
                    matching.delete()
                handled_names.add(name)
                continue

            self._validate_required(project_and_group, entity_name, rule_config)

            if matching:
                if self._needs_update(matching.asdict(), rule_config):
                    payload = self._payload_for_update(project, rule_config)
                    info(f"Editing {entity_name} of merge_requests_approval_rules in {project_and_group}")
                    project.approvalrules.update(matching.id, payload)
                else:
                    info(
                        f" * {entity_name} of merge_requests_approval_rules in {project_and_group}"
                        f" doesn't need an update."
                    )
            else:
                payload = self._payload_for_create(project, rule_config)
                info(f" * Adding {entity_name} of merge_requests_approval_rules in {project_and_group}")
                project.approvalrules.create(payload)
            handled_names.add(name)

        if enforce:
            for existing in existing_rules:
                if existing.name not in handled_names:
                    info(
                        f"Deleting rule '{existing.name}' of merge_requests_approval_rules"
                        f" in {project_and_group} as it's not in config and enforce is set to true."
                    )
                    existing.delete()

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
        gitlab_norm["protected_branches"] = sorted(b["name"] for b in gitlab_norm.get("protected_branches", []))

        # The update payload treats missing user_ids/group_ids/protected_branches
        # as "clear them", so mirror that here to keep the comparison honest.
        config_norm = dict(entity_in_configuration)
        config_norm["user_ids"] = sorted(config_norm.get("user_ids", []))
        config_norm["group_ids"] = sorted(config_norm.get("group_ids", []))
        config_norm["protected_branches"] = sorted(config_norm.get("protected_branches", []))

        return super()._needs_update(gitlab_norm, config_norm)

    @staticmethod
    def _payload_for_create(project: Project, rule_config: Dict) -> Dict:
        payload = dict(rule_config)
        if "protected_branches" in payload:
            branch_names = payload.pop("protected_branches")
            payload["protected_branch_ids"] = [project.protectedbranches.get(name).id for name in branch_names]
        return payload

    def _payload_for_update(self, project: Project, rule_config: Dict) -> Dict:
        payload = self._payload_for_create(project, rule_config)
        # GitLab interprets omitted user_ids/group_ids/protected_branch_ids as "no change",
        # but we want them to mean "clear them" so removals in config take effect.
        payload.setdefault("user_ids", [])
        payload.setdefault("group_ids", [])
        payload.setdefault("protected_branch_ids", [])
        return payload

    @staticmethod
    def _find_duplicates(project_and_group: str, configured_rules: Dict) -> None:
        seen: Dict[str, str] = {}
        for key, entry in configured_rules.items():
            name = entry.get("name")
            if name is None:
                continue
            if name in seen:
                critical(
                    f"Entities {seen[name]} and {key} in merge_requests_approval_rules for {project_and_group}"
                    f" are the same in terms of their defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)
            seen[name] = key

    @staticmethod
    def _validate_required(project_and_group: str, entity_name: str, rule_config: Dict) -> None:
        missing = [key for key in ("name", "approvals_required") if rule_config.get(key) is None]
        if missing:
            critical(
                f"Entity {entity_name} in merge_requests_approval_rules for {project_and_group}"
                f" doesn't have some of its keys required to create or update:"
                f" {', '.join(missing)}"
            )
            sys.exit(EXIT_INVALID_INPUT)
