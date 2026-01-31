from logging import debug
from typing import Any, cast
from gitlab.v4.objects import Project

from cli_ui import warning

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


class ProjectSecuritySettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_security_settings", gitlab)

    def _process_configuration(self, project_name: str, configuration: dict) -> None:
        project: Project = self.gl.get_project_by_path_cached(project_name)

        security_settings_in_config = configuration.get("project_security_settings", {})
        security_settings_in_gitlab = self.get_project_security_settings(project)

        if self._needs_update(security_settings_in_gitlab, security_settings_in_config):
            debug("Updating project security settings")
            self._update_project_security_settings(project, security_settings_in_gitlab, security_settings_in_config)
        else:
            debug("No update needed for project security settings")

    def get_project_security_settings(self, project: Project) -> dict:
        """Retrieve project security settings using python-gitlab."""
        try:
            # TODO: python-gitlab does not yet support retrieving project security settings
            # via its dedicated manager, so we use a lower-level http_get method here.
            # Switch to native method once supported by python-gitlab.

            path = f"/projects/{project.id}/security_settings"
            result = self.gl.http_get(path)
            # http_get can return Response for streamed requests, but we're not streaming
            # so it will always be a dict
            return cast(dict[str, Any], result)
        except Exception as e:
            warning(f"Failed to get project security settings for project {project.path_with_namespace}: {e}")
            return {}

    def _update_project_security_settings(self, project: Project, initial_settings: dict, bsettings: dict) -> None:
        """Update project security settings using python-gitlab."""
        try:
            # TODO: python-gitlab does not yet support updating project security settings
            # via its dedicated manager, so we use a lower-level http_put method here.
            # Switch to native method once supported by python-gitlab.
            debug(initial_settings)
            debug("project_security_settings BEFORE: ^^^")
            path = f"/projects/{project.id}/security_settings"
            updated_security_config = self.gl.http_put(path, post_data=settings)
            debug(cast(dict[str, Any], updated_security_config))
            debug("project_security_settings AFTER: ^^^")
        except Exception as e:
            warning(f"Failed to update project security settings for project {project.path_with_namespace}: {e}")

    def _print_diff(self, project_or_project_and_group: str, entity_config, diff_only_changed: bool):
        project = self.gl.get_project_by_path_cached(project_or_project_and_group)
        entity_in_gitlab = self.get_project_security_settings(project)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )
