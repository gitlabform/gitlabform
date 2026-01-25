from logging import debug
from typing import Any, cast
from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


class ProjectSecuritySettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_security_settings", gitlab)

    def _process_configuration(self, project_name: str, configuration: dict) -> None:
        debug("Processing project security settings...")
        project: Project = self.gl.get_project_by_path_cached(project_name)

        security_settings_in_config = configuration.get("project_security_settings", {})
        security_settings_in_gitlab = self.get_project_security_settings(project_name)
        debug(security_settings_in_gitlab)
        debug("project_security_settings BEFORE: ^^^")

        if self._needs_update(security_settings_in_gitlab, security_settings_in_config):
            debug("Updating project security settings")
            self._update_project_security_settings(project, security_settings_in_config)
            debug("project_security_settings AFTER: ^^^")
        else:
            debug("No update needed for project security settings")

    def get_project_security_settings(self, project_path: str) -> dict:
        """Get project security settings from GitLab using python-gitlab."""
        project: Project = self.gl.get_project_by_path_cached(project_path)
        # Use lower-level http_get as security_settings doesn't have a dedicated manager
        path = f"/projects/{project.encoded_id}/security_settings"
        result = self.gl.http_get(path)
        # http_get can return Response for streamed requests, but we're not streaming
        # so it will always be a dict
        return cast(dict[str, Any], result)

    def _update_project_security_settings(self, project: Project, settings: dict) -> None:
        """Update project security settings using python-gitlab."""
        path = f"/projects/{project.encoded_id}/security_settings"
        self.gl.http_put(path, post_data=settings)

    def _print_diff(self, project_or_project_and_group: str, entity_config, diff_only_changed: bool):
        entity_in_gitlab = self.get_project_security_settings(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )
