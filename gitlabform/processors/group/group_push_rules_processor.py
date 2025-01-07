from logging import info, debug
from typing import Dict

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

from gitlab.v4.objects.groups import Group
from gitlab.exceptions import GitlabGetError


class GroupPushRulesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_push_rules", gitlab)

    def _process_configuration(self, group: str, configuration: Dict):
        configured_group_push_rules = configuration.get("group_push_rules", {})

        gitlab_group: Group = self.gl.get_group_by_path_cached(group)

        try:
            existing_push_rules = gitlab_group.pushrules.get()
        except GitlabGetError as e:
            if e.response_code == 404:
                debug(
                    f"No existing push rules for {gitlab_group.name}, creating new push rules."
                )
                self.create_group_push_rules(gitlab_group, configured_group_push_rules)
                return

        if self._needs_update(
            existing_push_rules.asdict(), configured_group_push_rules
        ):
            debug(f"Updating group push rules for group {gitlab_group.name}")
            self.update_group_push_rules(
                existing_push_rules, configured_group_push_rules
            )
        else:
            debug("No update needed for Group Push Rules")

    @staticmethod
    def update_group_push_rules(push_rules, configured_group_push_rules: dict):
        for key, value in configured_group_push_rules.items():
            debug(f"Updating setting {key} to value {value}")
            setattr(push_rules, key, value)
        push_rules.save()

    @staticmethod
    def create_group_push_rules(gitlab_group, push_rules_config: Dict):
        debug(f"Creating push rules with configuration: {push_rules_config}")
        gitlab_group.pushrules.create(push_rules_config)
