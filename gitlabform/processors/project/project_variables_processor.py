from typing import Dict, Any, List, cast
from cli_ui import debug as verbose
from cli_ui import warning

import copy
import textwrap
import ez_yaml

from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Project, ProjectVariable
from gitlabform.gitlab import GitLab
from gitlabform.processors.util.difference_logger import hide
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.variables_processor import VariablesProcessor


class ProjectVariablesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("variables", gitlab)
        self._variables_processor = VariablesProcessor(self._needs_update)

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        configured_variables = configuration.get("variables", {})
        enforce_mode: bool = configured_variables.get("enforce", False)

        if enforce_mode:
            verbose(f"Enforce mode enabled for variables in {project_and_group}")
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

    def _print_diff(
        self,
        project_and_group: str,
        configuration: Dict[str, Any],
        diff_only_changed: bool = False,
    ) -> None:
        """Print current and configured variables for comparison."""
        try:
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            current_variables: List[ProjectVariable] = self._variables_processor.get_variables_from_gitlab(project)
            variables_list: list[Dict[str, str]] = []

            for variable in current_variables:
                var_dict = {
                    "key": variable.key,
                    "value": hide(variable.value),
                }
                if hasattr(variable, "environment_scope"):
                    var_dict["environment_scope"] = variable.environment_scope
                variables_list.append(var_dict)

            verbose(f"Variables for {project_and_group} in GitLab:")
            verbose(
                textwrap.indent(
                    ez_yaml.to_string(variables_list),
                    "  ",
                )
            )
        except GitlabGetError:
            verbose(f"Variables for {project_and_group} in GitLab cannot be checked.")

        verbose(f"Variables in {project_and_group} in configuration:")

        configured_variables = copy.deepcopy(configuration)
        enforce_variables = configured_variables.get("enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "variable"
        if enforce_variables:
            configured_variables.pop("enforce")

        for key in configured_variables.keys():
            configured_variables[key]["value"] = hide(configured_variables[key]["value"])

        verbose(
            textwrap.indent(
                ez_yaml.to_string(configured_variables),
                "  ",
            )
        )
