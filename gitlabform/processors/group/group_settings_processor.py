import os
from logging import info, debug, warning
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

        # Remove avatar from config to process it last
        avatar_config = configured_group_settings.pop("avatar", None)

        # Process other settings first
        if self._needs_update(gitlab_group.asdict(), configured_group_settings):
            info(f"Updating group settings for group {gitlab_group.name}")
            self.update_group_settings(gitlab_group, configured_group_settings)
        else:
            debug("No update needed for Group Settings")

        # Process avatar last - with error handling that doesn't stop execution
        if avatar_config is not None:
            try:
                self._process_group_avatar(gitlab_group, {"avatar": avatar_config})
            except Exception as e:
                warning(f"Failed to process group avatar: {e}")
                raise e

    @staticmethod
    def update_group_settings(gitlab_group: Group, group_settings_config: dict):
        for key in group_settings_config:
            value = group_settings_config[key]
            debug(f"Updating setting {key} to value {value}")
            gitlab_group.__setattr__(key, value)
            gitlab_group.save()

    def _process_group_avatar(self, gitlab_group: Group, group_settings_config: dict) -> None:
        """Process group avatar settings from configuration."""
        debug("Processing group avatar configuration")

        avatar_path = group_settings_config.get("avatar")
        if avatar_path is None:
            debug("No avatar configuration provided, skipping avatar processing")
            return

        debug(f"Avatar configuration found: {avatar_path}")

        # Check current avatar status
        current_avatar = getattr(gitlab_group, "avatar_url", None)

        if avatar_path == "":
            # Want to remove avatar
            if not current_avatar:
                debug("Avatar already empty, no update needed")
                return
            debug("Deleting group avatar")
            gitlab_group.avatar = ""
            gitlab_group.save()
            debug("Avatar deleted successfully")
            return

        # Resolve relative paths to absolute paths
        if not os.path.isabs(avatar_path):
            # Convert relative path to absolute path relative to current working directory
            avatar_path = os.path.abspath(avatar_path)
            debug(f"Resolved relative path to absolute path: {avatar_path}")

        # Want to set avatar from file
        debug(f"Setting group avatar from file: {avatar_path}")
        try:
            with open(avatar_path, "rb") as avatar_file:
                gitlab_group.avatar = avatar_file
                gitlab_group.save()
            debug("Group avatar uploaded successfully")
        except FileNotFoundError:
            error_msg = f"Group avatar file not found: {avatar_path}"
            debug(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Error uploading group avatar: {str(e)}"
            debug(error_msg)
            raise Exception(error_msg) from e
