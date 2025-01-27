from logging import debug
from typing import Callable
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger

from gitlab.v4.objects import Project


class ProjectSettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_settings", gitlab)
        self.get_entity_in_gitlab: Callable = getattr(self, "get_project_settings")

    def _process_configuration(self, project_path: str, configuration: dict):
        debug("Processing project settings...")
        project: Project = self.gl.get_project_by_path_cached(project_path)

        project_settings_in_config = configuration.get("project_settings", {})
        project_settings_in_gitlab = project.asdict()
        debug(project_settings_in_gitlab)
        debug(f"project_settings BEFORE: ^^^")

        if self._needs_update(project_settings_in_gitlab, project_settings_in_config):
            debug("Updating project settings")
            for key, value in project_settings_in_config.items():
                debug(f"Updating setting {key} to value {value}")
                setattr(project, key, value)
            project.save()

            debug(project.asdict())
            debug(f"project_settings AFTER: ^^^")

        else:
            debug("No update needed for project settings")

    def get_project_settings(self, project_path: str):
        # return self.get_entity_in_gitlab(project_path)
        return self.gl.get_project_by_path_cached(project_path).asdict()

    def _print_diff(
        self, project_or_project_and_group: str, entity_config, diff_only_changed: bool
    ):
        entity_in_gitlab = self.get_project_settings(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )
