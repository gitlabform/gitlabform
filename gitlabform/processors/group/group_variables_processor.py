from typing import Any, Dict
from cli_ui import debug as verbose
from gitlabform.gitlab import GitLab
from gitlab.v4.objects import Group

from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.variables_processor import VariablesProcessor


class GroupVariablesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_variables", gitlab)
        self._variables_processor = VariablesProcessor(self._needs_update)

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        group: Group = self.gl.get_group_by_path_cached(project_and_group)

        configured_variables = configuration.get("group_variables", {})
        enforce_mode: bool = configured_variables.get("enforce", False)

        if enforce_mode:
            verbose(f"Enforce mode enabled for variables in {project_and_group}")
            # Remove 'enforce' key from the config so that it's not treated as a variable
            configured_variables.pop("enforce")

        self._variables_processor.process_variables(group, configured_variables, enforce_mode)
