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
        self.get_entity_in_gitlab = self._get_variables_in_gitlab

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

    def _get_variables_in_gitlab(self, project_and_group: str) -> Dict[str, Dict[str, Any]]:
        try:
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            variables = self._variables_processor.get_variables_from_gitlab(project)
        except GitlabGetError:
            return {}

        return {self._variable_identity(v.asdict()): self._masked_variable(v.asdict()) for v in variables}

    def _prepare_entities_for_diff(
        self,
        entity_in_gitlab: dict,
        entity_config: dict,
    ) -> tuple[dict, dict]:
        # Config-side is keyed by user-chosen aliases and includes an "enforce" flag; normalize
        # it to the same key@scope identity used for the GitLab side so keys line up.
        normalized_config = {
            self._variable_identity(var): self._masked_variable(var)
            for alias, var in entity_config.items()
            if alias != "enforce" and isinstance(var, dict)
        }
        return entity_in_gitlab, normalized_config

    @staticmethod
    def _variable_identity(var: Dict[str, Any]) -> str:
        return f"{var.get('key')}@{var.get('environment_scope', '*')}"

    @staticmethod
    def _masked_variable(var: Dict[str, Any]) -> Dict[str, Any]:
        masked = {k: v for k, v in var.items() if k not in {"id", "_links"}}
        if "value" in masked:
            masked["value"] = hide(str(masked["value"]))
        return masked
