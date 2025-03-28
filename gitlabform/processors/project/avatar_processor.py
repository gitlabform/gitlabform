from cli_ui import debug
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class AvatarProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project", gitlab)

    def _process_configuration(self, project_and_group, configuration):
        # Get the project configuration
        project_config = configuration.get("project")
        if not project_config or not isinstance(project_config, dict):
            return  # No project config

        # Check if 'avatar' is explicitly set in the configuration
        if "avatar" not in project_config:
            return  # Avatar is not defined in the configuration

        # Get the avatar value
        avatar_path = project_config.get("avatar")

        if avatar_path:
            # If there is a path, update the avatar
            debug(f"Setting avatar for {project_and_group}...")
            self.gitlab.update_project_avatar(project_and_group, avatar_path)
            debug(f"✅ Avatar updated for {project_and_group}")
        else:
            # If the value is an empty string, remove the avatar
            debug(f"Removing avatar for {project_and_group}...")
            self.gitlab.delete_project_avatar(project_and_group)
            debug(f"✅ Avatar removed for {project_and_group}")
