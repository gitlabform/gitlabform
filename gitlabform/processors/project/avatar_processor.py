from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
import os
from pathlib import Path
from cli_ui import debug, warning


class AvatarProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_avatar", gitlab)

    def _process_configuration(self, project_and_group, configuration):
        project = self.gl.get_project_by_path_cached(project_and_group)

        # Check if configuration is a dict with 'delete' key
        if isinstance(configuration, dict) and configuration.get("delete"):
            debug(f"Removing avatar for project {project_and_group}...")

            # Set avatar to None to remove it
            project.avatar = None
            project.save()

            debug(f"✅ Avatar removed for project {project_and_group}")
            return

        if isinstance(configuration, str):
            avatar_path = configuration
            full_path = self._get_effective_path(avatar_path)

            # Check if file exists
            if not os.path.exists(full_path):
                warning(f"❌ Avatar file not found: {full_path}")
                return

            # Update the avatar
            debug(f"Setting avatar for project {project_and_group}...")

            # Update the avatar
            with open(full_path, "rb") as avatar_file:
                project.avatar = avatar_file
                project.save()

            debug(f"✅ Avatar updated for project {project_and_group}")

    def _get_effective_path(self, path_str):
        path = Path(path_str)
        if path.is_absolute():
            return str(path)
        else:
            return str(Path(os.path.abspath(path_str)))
