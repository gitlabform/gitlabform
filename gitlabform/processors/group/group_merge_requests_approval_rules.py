from logging import debug
from typing import Dict

from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.gitlab import GitLab
from gitlab.v4.objects.groups import Group
from gitlab.exceptions import GitlabGetError, GitlabCreateError, GitlabUpdateError


class GroupMergeRequestsApprovalRules(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_merge_requests_approval_rules", gitlab)

    def _process_configuration(self, group_path: str, configuration: Dict):
        configured_mr_rules = configuration.get(
            "group_merge_requests_approval_rules", {}
        )
        group: Group = self.gl.get_group_by_path_cached(group_path)

        try:
            existing_mr_rules = {
                rule.name: rule for rule in group.approval_rules.list()
            }
        except GitlabGetError as e:
            debug(f"Error retrieving existing approval rules: {e}")
            raise

        for rule_config in configured_mr_rules.values():
            rule_name = rule_config.get("name")
            rule_config = rule_config.copy()

            if rule_name in existing_mr_rules:
                existing_rule = existing_mr_rules[rule_name]
                if self._needs_update(existing_rule.asdict(), rule_config):
                    self._update_rule(existing_rule, rule_config)
            else:
                self._create_rule(group, rule_config)

    def _create_rule(self, group: Group, rule_config: Dict):
        try:
            group.approval_rules.create(rule_config)
        except GitlabCreateError as e:
            debug(f"Failed to create approval rule '{rule_config['name']}': {e}")
            raise

    def _update_rule(self, existing_rule, rule_config: Dict):
        try:
            for key, value in rule_config.items():
                setattr(existing_rule, key, value)
            existing_rule.save()
        except GitlabUpdateError as e:
            debug(f"Failed to update approval rule '{existing_rule.name}': {e}")
            raise
