from typing import Dict, Any
from logging import warning, info

from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.util.difference_logger import hide
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.variables_processor import VariablesProcessor


class ProjectVariablesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, log_level: int):
        super().__init__("variables", gitlab)
        self.log_level = log_level
        self._variables_processor = VariablesProcessor(self._needs_update)

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        configured_variables = configuration.get("variables", {})
        enforce_mode: bool = configured_variables.get("enforce", False)

        if enforce_mode:
            info(f"Enforce mode enabled for variables in {project_and_group}")
            # Remove 'enforce' key from the config so that it's not treated as a variable
            configured_variables.pop("enforce")

        self._variables_processor.process_variables(project, configured_variables, enforce_mode)

    def _can_proceed(self, project_or_group: str, configuration: Dict[str, Any]) -> bool:
        """Check if builds are enabled for the project."""
        try:
            project: Project = self.gl.get_project_by_path_cached(project_or_group)
            if project.builds_access_level == "disabled":
                warning("Builds disabled in this project so I can't set variables here.")
                return False
            return True
        except GitlabGetError:
            warning(f"Cannot get project settings for {project_or_group}")
            return False

    def _get_current_state(self, project_and_group: str) -> Dict[str, Dict[str, Any]]:
        try:
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            variables = self._variables_processor.get_variables_from_gitlab(project)
        except GitlabGetError:
            variables = []

        return {self._variable_identity(v.asdict()): self._masked_variable(v.asdict()) for v in variables}

    def _get_desired_state(self, entity_config: dict) -> Dict[str, Dict[str, Any]]:
        # Config is keyed by user-chosen aliases and includes an "enforce" flag; normalize
        # it to the same key@scope identity used for the current state so keys line up.
        return {
            self._variable_identity(var): self._masked_variable(var)
            for alias, var in entity_config.items()
            if alias != "enforce" and isinstance(var, dict)
        }

    @staticmethod
    def _variable_identity(var: Dict[str, Any]) -> str:
        """Compose a stable diff key. GitLab allows the same variable key on multiple
        environment scopes, so `key` alone is not unique; `key@scope` is."""
        return f"{var.get('key')}@{var.get('environment_scope', '*')}"

    @staticmethod
    def _masked_variable(var: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a variable for diff output. Drops `id`/`_links` (GitLab-side noise
        that would always show as spurious differences) and masks `value` so secrets
        don't end up in the log."""
        masked = {k: v for k, v in var.items() if k not in {"id", "_links"}}
        if "value" in masked:
            masked["value"] = hide(str(masked["value"]))
        return masked
