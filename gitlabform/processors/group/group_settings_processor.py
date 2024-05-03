from logging import info, debug
from typing import Dict

from gitlabform.gitlab import GitLab
from gitlab.v4.objects.groups import Group
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_settings", gitlab)

    def _process_configuration(self, group: str, configuration: Dict):
        configured_group_settings = configuration.get("group_settings", {})

        gitlab_group: Group = self.gl.get_group_by_path_cached(group)

        if self._needs_update(gitlab_group.asdict(), configured_group_settings):
            info(f"Updating group settings for group {gitlab_group.name}")
            self.update_group_settings(gitlab_group, configured_group_settings)
        else:
            debug("No update needed for Group Settings")

    @staticmethod
    def update_group_settings(gitlab_group: Group, group_settings_config: dict):
        for key in group_settings_config:
            value = group_settings_config[key]
            debug(f"Updating setting {key} to value {value}")
            gitlab_group.__setattr__(key, value)
            gitlab_group.save()
