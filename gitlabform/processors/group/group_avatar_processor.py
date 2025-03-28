from cli_ui import debug
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupAvatarProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group", gitlab)

    def _process_configuration(self, group, configuration):
        # Get the group configuration
        group_config = configuration.get("group")
        if not group_config or not isinstance(group_config, dict):
            return  # No group config

        # Check if 'avatar' is explicitly set in the configuration
        if "avatar" not in group_config:
            return  # Avatar is not defined in the configuration

        # Get the avatar value
        avatar_path = group_config.get("avatar")

        if avatar_path:
            # If there is a path, update the avatar
            debug(f"Setting avatar for group {group}...")
            self.gitlab.update_group_avatar(group, avatar_path)
            debug(f"✅ Avatar updated for group {group}")
        else:
            # If the value is explicitly an empty string, remove the avatar
            debug(f"Removing avatar for group {group}...")
            self.gitlab.delete_group_avatar(group)
            debug(f"✅ Avatar removed for group {group}")
