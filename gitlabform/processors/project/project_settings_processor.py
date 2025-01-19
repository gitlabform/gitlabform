from logging import debug

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

from gitlab.v4.objects import Project


class ProjectSettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_settings", gitlab)

    def _process_configuration(self, project_path: str, configuration: dict):
        debug("Processing project settings...")
        project: Project = self.gl.get_project_by_path_cached(project_path)

        project_settings_in_config = configuration.get("project_settings", {})
        project_settings_in_gitlab = project.asdict()

        if self._needs_update(project_settings_in_gitlab, project_settings_in_config):
            debug("Updating project settings")
            for key, value in project_settings_in_config.items():
                debug(f"Updating setting {key} to value {value}")
                setattr(project, key, value)

            project.save()
        else:
            debug("No update needed for project settings")
