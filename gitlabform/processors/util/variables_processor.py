from cli_ui import debug as verbose
from cli_ui import warning
from typing import Dict, List, Any, Set, Tuple, Callable, cast, overload

from gitlab.v4.objects import Group, Project, GroupVariable, ProjectVariable


class VariablesProcessor:
    def __init__(self, needs_update: Callable):
        self.needs_update: Callable = needs_update

    @overload
    def get_variables_from_gitlab(self, group_or_project: Group) -> List[GroupVariable]: ...

    @overload
    def get_variables_from_gitlab(self, group_or_project: Project) -> List[ProjectVariable]: ...

    def get_variables_from_gitlab(
        self, group_or_project: Group | Project
    ) -> List[GroupVariable] | List[ProjectVariable]:
        """Get variables as a properly typed list."""
        variables = group_or_project.variables.list(get_all=True)

        if isinstance(group_or_project, Project):
            return [cast(ProjectVariable, var) for var in variables]  # Return type is List[ProjectVariable]
        else:
            return [cast(GroupVariable, var) for var in variables]  # Return type is List[GroupVariable]

    def _variables_match(self, existing_var: Dict[str, Any], config_var: Dict[str, Any]) -> bool:
        """Compare if existing variable matches the configured attributes."""
        # Ignore internal GitLab attributes and delete flag
        ignore_keys = {"id", "_links", "delete"}

        # Check if all configured attributes match existing variable
        return all(existing_var.get(key) == value for key, value in config_var.items() if key not in ignore_keys)

    def process_variables(
        self,
        group_or_project: Group | Project,
        configured_variables: Dict,
        enforce: bool,
    ) -> None:
        """Process variables configuration for a project or group."""
        try:
            # Get existing variables
            existing_variables = self.get_variables_from_gitlab(group_or_project)
            verbose(f"Found {len(existing_variables)} existing variables in {group_or_project.name}")

            # Process configured variables
            processed_vars = set()
            if configured_variables:
                verbose(f"Processing {len(configured_variables)} variables from configuration")
                for var_config in configured_variables.values():
                    self._handle_variable(group_or_project, var_config, existing_variables)
                    processed_vars.add((var_config["key"], var_config.get("environment_scope", "*")))

            # Handle enforce mode
            if enforce and existing_variables:
                self._handle_enforce_mode(group_or_project, existing_variables, processed_vars)

        except Exception as err:
            warning(f"Failed to process variables for {group_or_project.name}: {str(err)}")
            raise

    def _handle_variable(
        self,
        group_or_project: Group | Project,
        var_config: Dict[str, Any],
        existing_variables: List[GroupVariable] | List[ProjectVariable],
    ) -> None:
        """Handle a single variable operation."""
        key = var_config["key"]
        scope = var_config.get("environment_scope", "*")
        should_delete = var_config.get("delete", False)

        # Find matching existing variable
        existing_var = next(
            (
                existing_var
                for existing_var in existing_variables
                if existing_var.key == key and getattr(existing_var, "environment_scope", "*") == scope
            ),
            None,
        )

        if not existing_var:
            # In case config refers to deleting non-existent variable, raise error
            if should_delete:
                raise Exception(f"Cannot delete variable '{key}' with scope '{scope}' - variable does not exist")
            self._create_variable(group_or_project, var_config)
            return
        else:
            # If the variable exists, check if it should be deleted or updated
            if should_delete:
                # If delete is requested, check if the variable matches the config
                # and delete it if it does
                if not self._variables_match(existing_var.asdict(), var_config):
                    raise Exception(f"Cannot delete {key} - attributes don't match")
                self._delete_variable(group_or_project, key, scope)
                return
            else:
                # If delete is not requested, update the variable if config is different from gitlab
                if self.needs_update(existing_var.asdict(), var_config):
                    self._update_variable(group_or_project, var_config)
                    return
                else:
                    verbose(f"Variable {key} with scope {scope} already matches configuration, no update needed")
                    return

    def _handle_enforce_mode(
        self,
        group_or_project: Group | Project,
        existing_variables: List[GroupVariable] | List[ProjectVariable],
        processed_vars: Set[Tuple[str, str]],
    ) -> None:
        """Delete variables not in configuration when enforce mode is enabled."""
        vars_to_delete = [
            existing_var
            for existing_var in existing_variables
            if (existing_var.key, getattr(existing_var, "environment_scope", "*")) not in processed_vars
        ]

        if vars_to_delete:
            verbose(f"Enforce mode will delete {len(vars_to_delete)} variables")
            for var in vars_to_delete:
                self._delete_variable(group_or_project, var.key, getattr(var, "environment_scope", "*"))

    def _create_variable(self, group_or_project: Group | Project, var_config: Dict[str, Any]) -> None:
        """Create a new variable."""
        attrs = var_config.copy()
        verbose(f"Creating variable {attrs['key']}")
        group_or_project.variables.create(attrs)

    def _update_variable(self, group_or_project: Group | Project, var_config: Dict[str, Any]) -> None:
        """Update an existing variable."""
        attrs = var_config.copy()
        scope = attrs.get("environment_scope", "*")
        verbose(f"Updating variable {attrs['key']}")
        group_or_project.variables.update(attrs["key"], attrs, filter={"environment_scope": scope})

    def _delete_variable(self, group_or_project: Group | Project, key: str, scope: str) -> None:
        """Delete a variable."""
        verbose(f"Deleting variable {key}")
        group_or_project.variables.delete(key, filter={"environment_scope": scope})
