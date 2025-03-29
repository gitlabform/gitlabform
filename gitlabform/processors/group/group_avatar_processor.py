from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
import os
from pathlib import Path
from cli_ui import debug, warning


class GroupAvatarProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_avatar", gitlab)

    def _process_configuration(self, group_path, configuration):
        if "*" in group_path:
            # Remove the wildcard as we're dealing with the group itself
            group_path = group_path.rstrip("/*")

        group = self.gl.groups.get(group_path)

        # Check if configuration is a dict with 'delete' key
        if isinstance(configuration, dict) and configuration.get("delete"):
            debug(f"Removing avatar for group {group_path}...")

            # Set avatar to None to remove it
            group.avatar = None
            group.save()

            debug(f"✅ Avatar removed for group {group_path}")
            return

        if isinstance(configuration, str):
            avatar_path = configuration
            full_path = self._get_effective_path(avatar_path)

            # Check if file exists
            if not os.path.exists(full_path):
                warning(f"❌ Avatar file not found: {full_path}")
                return

            # Update the avatar
            debug(f"Setting avatar for group {group_path}...")

            # Update the avatar
            with open(full_path, "rb") as avatar_file:
                group.avatar = avatar_file
                group.save()

            debug(f"✅ Avatar updated for group {group_path}")

    def _get_effective_path(self, path_str):
        path = Path(path_str)
        if path.is_absolute():
            return str(path)
        else:
            return str(Path(os.path.abspath(path_str)))
