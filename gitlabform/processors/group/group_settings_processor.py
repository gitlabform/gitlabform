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

        # Process avatar separately before other settings
        self._process_group_avatar(gitlab_group, configured_group_settings)

        # Remove avatar from config to prevent it from being processed in the standard way
        if "avatar" in configured_group_settings:
            configured_group_settings = configured_group_settings.copy()
            del configured_group_settings["avatar"]

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

    def _process_group_avatar(self, gitlab_group: Group, group_settings_config: dict) -> None:
        """Process group avatar settings from configuration."""
        avatar_path = group_settings_config.get("avatar")
        if avatar_path is None:
            return

        debug(f"Processing group avatar configuration: {avatar_path}")

        if avatar_path == "":
            debug("Deleting group avatar")
            gitlab_group.avatar = ""
            gitlab_group.save()
            debug("Avatar deleted successfully")
            return

        debug(f"Setting group avatar from file: {avatar_path}")
        try:
            with open(avatar_path, "rb") as avatar_file:
                gitlab_group.avatar = avatar_file
                gitlab_group.save()
            debug("Group avatar uploaded successfully")
        except FileNotFoundError:
            debug(f"Group avatar file not found: {avatar_path}")
        except Exception as e:
            debug(f"Error uploading group avatar: {str(e)}")
