from cli_ui import debug
from gitlabform.processors.abstract_processor import AbstractProcessor
import os
from pathlib import Path


class AvatarProcessor(AbstractProcessor):
    def __init__(self, gitlab, config):
        super().__init__("project_avatar", gitlab)
        self.gitlab_api = gitlab.gitlab
        self.config = config  # Store the configuration instance

    def _process_configuration(self, project_and_group, configuration):
        # Check if configuration is a dictionary with 'delete' key
        if isinstance(configuration, dict) and "delete" in configuration:
            if configuration["delete"]:
                # Delete the avatar
                debug(f"Removing avatar for project {project_and_group}...")

                # Get project object using python-gitlab
                gitlab_project = self.gitlab_api.projects.get(project_and_group)

                # Remove the avatar
                gitlab_project.avatar = None
                gitlab_project.save()

                debug(f"✅ Avatar removed for project {project_and_group}")
            return

        # Otherwise, it should be a path to an avatar image
        avatar_path = configuration

        if avatar_path and isinstance(avatar_path, str):
            # Handle both absolute and relative paths, with relative paths being relative to config location
            path_as_path = Path(str(avatar_path))
            if path_as_path.is_absolute():
                effective_path = path_as_path
            else:
                # Relative paths are relative to config file location
                effective_path = Path(os.path.join(self.config.config_dir, str(path_as_path)))

            full_path = str(effective_path)

            # Check if file exists
            if not os.path.exists(full_path):
                debug(f"❌ Avatar file not found: {full_path}")
                return

            # If there is a path, update the avatar
            debug(f"Setting avatar for project {project_and_group}...")

            # Get project object
            gitlab_project = self.gitlab_api.projects.get(project_and_group)

            # Update the avatar
            with open(full_path, "rb") as avatar_file:
                gitlab_project.avatar = avatar_file
                gitlab_project.save()

            debug(f"✅ Avatar updated for project {project_and_group}")
