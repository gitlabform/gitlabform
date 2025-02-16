from typing import Dict, Any, Set, Tuple
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


class VariablesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("variables", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        """Process variables configuration for a project.
        
        This method:
        1. Retrieves current variables from the project
        2. Processes configured variables (create/update/delete)
        3. Handles enforce mode if enabled (deletes unconfigured variables)
        4. Supports environment-scoped variables
        5. Supports all GitLab API variable attributes
        
        Args:
            project_and_group: Project path
            configuration: Project configuration dictionary
        """
        try:
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            current_variables: list[ProjectVariable] = project.variables.list()
            
            configured_variables = configuration.get("variables", {})
            enforce_mode: bool = configured_variables.get("enforce", False)

            if enforce_mode:
                verbose(f"Enforce mode enabled for variables in {project_and_group}")
                # Remove 'enforce' key from the config so that it's not treated as a variable
                configured_variables.pop("enforce")

            # Create a lookup dictionary for faster access to existing variables
            current_vars_lookup = {
                (var.key, getattr(var, "environment_scope", "*")): var
                for var in current_variables
            }

            # Log the current state
            verbose(f"Found {len(current_variables)} existing variables in {project_and_group}")
            verbose(f"Processing {len(configured_variables)} variables from configuration")
            
            # Process variables if any are configured
            processed_vars = set()
            if configured_variables:
                processed_vars = self._process_variables(project, configured_variables, current_vars_lookup)

            # Handle enforce mode (even if no variables are configured)
            if enforce_mode:
                unprocessed_count = len(current_variables) - len(processed_vars)
                if unprocessed_count > 0:
                    verbose(
                        f"Enforce mode will delete {unprocessed_count} variables "
                        f"not in configuration from {project_and_group}"
                    )
                self._delete_unconfigured_variables(current_variables, processed_vars)

        except Exception as e:
            warning(f"Failed to process variables for {project_and_group}: {str(e)}")

    def _process_variables(
        self,
        project: Project,
        configured_variables: Dict[str, Any],
        current_vars_lookup: Dict[Tuple[str, str], ProjectVariable],
    ) -> Set[Tuple[str, str]]:
        """Process all variables defined in the configuration.
        
        This method:
        1. Iterates through each variable in the configuration
        2. Processes all attributes defined in the configuration
        3. Tracks each variable being processed, including those marked for deletion
        4. Calls _handle_variable to perform the actual operation (create/update/delete)
        
        Args:
            project: GitLab project object
            configured_variables: Dictionary of variable configurations
                Format: {
                    "var_name": {
                        "key": "VAR_NAME",        # required
                        "value": "value",         # required
                        "environment_scope": "*", # optional, defaults to "*"
                        "protected": true,        # optional
                        "masked": true,           # optional
                        "variable_type": "env_var", # optional
                        # ... any other attributes supported by GitLab API
                        "delete": true/false      # optional
                    }
                }
            current_vars_lookup: Dictionary mapping (key, scope) to existing ProjectVariable objects
        
        Returns:
            Set of tuples (variable_key, environment_scope) that were processed.
        
        Note:
            - Variables marked for deletion are included in the returned set
            - Multiple variables with the same key but different environment scopes
              are treated as separate variables
            - All GitLab API supported attributes can be configured
        """
        processed_vars: Set[Tuple[str, str]] = set()

        for var_name, var_config in configured_variables.items():
            key: str = var_config["key"]
            env_scope: str = var_config.get("environment_scope", "*")
            
            processed_vars.add((key, env_scope))
            
            # Handle the variable with all its configured attributes
            self._handle_variable(project, var_config, current_vars_lookup)

        return processed_vars

    def _handle_variable(
        self,
        project: Project,
        var_config: Dict[str, Any],
        current_vars_lookup: Dict[Tuple[str, str], ProjectVariable],
    ) -> None:
        """Handle a single variable: create, update, or delete.
        
        Args:
            project: GitLab project object
            var_config: Complete variable configuration including all attributes
            current_vars_lookup: Dictionary mapping (key, scope) to existing ProjectVariable objects
            
        Note:
            - Uses filter parameter with environment_scope for unique identification
            - Supports all GitLab API variable attributes
            - Uses _needs_update to determine if update is needed
        """
        key: str = var_config["key"]
        env_scope: str = var_config.get("environment_scope", "*")
        should_delete: bool = var_config.get("delete", False)

        # Look up existing variable using the lookup dictionary
        existing_var = current_vars_lookup.get((key, env_scope))

        if existing_var:
            if should_delete:
                verbose(f"Deleting variable {key} with scope {env_scope}")
                project.variables.delete(key, filter={"environment_scope": env_scope})
            else:
                # Create variable configuration without special keys
                variable_attributes = var_config.copy()
                variable_attributes.pop("delete", None)
                variable_attributes.pop("key", None)
                env_scope = variable_attributes.pop("environment_scope", "*")

                if self._needs_update(existing_var.asdict(), variable_attributes):
                    verbose(f"Updating variable {key} with scope {env_scope}")
                    project.variables.update(
                        key,
                        variable_attributes,
                        filter={"environment_scope": env_scope}
                    )
        elif not should_delete:
            verbose(f"Creating new variable {key} with scope {env_scope}")
            variable_attributes = var_config.copy()
            variable_attributes.pop("delete", None)
            project.variables.create(variable_attributes)

    def _delete_unconfigured_variables(
        self,
        current_variables: list[ProjectVariable],
        processed_vars: Set[Tuple[str, str]],
    ) -> None:
        """Delete variables that are not in the configuration when enforce mode is enabled."""
        for var in current_variables:
            var_key = (var.key, getattr(var, "environment_scope", "*"))
            if var_key not in processed_vars:
                var.delete()

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
        self, project_and_group: str, configuration: Dict[str, Any], diff_only_changed: bool = False
    ) -> None:
        """Print current and configured variables for comparison."""
        try:
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            current_variables: list[ProjectVariable] = project.variables.list()
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

