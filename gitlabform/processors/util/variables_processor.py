from cli_ui import debug as verbose
from cli_ui import warning
from typing import Dict, List, Any, Set, Tuple, Callable, cast, overload

from gitlab.v4.objects import Group, Project, GroupVariable, ProjectVariable


class VariablesProcessor:

    def __init__(self, needs_update: Callable):
        self.needs_update: Callable = needs_update

    # Overload *variants* for 'get_variables_from_gitlab'.
    # These variants give extra information to the type checker.
    # They are ignored at runtime.
    # See: https://mypy.readthedocs.io/en/stable/cheat_sheet_py_typed.html#overloading
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

    def _create_lookup_key(self, attributes: Dict[str, Any], is_config: bool = False) -> Tuple[str, str]:
        """Create a lookup key from variable attributes.
        
        Args:
            attributes: Dictionary of variable attributes
            is_config: Boolean indicating if these are attributes from config (True) 
                      or from existing GitLab variable (False)
        
        Returns:
            Tuple of (key, environment_scope) for consistent lookup
        """
        return (
            attributes['key'],
            attributes.get('environment_scope', '*')
        )

    def _variables_match(self, existing_var: Dict[str, Any], config_var: Dict[str, Any]) -> bool:
        """Compare if existing variable matches the configured attributes.
        
        Args:
            existing_var: Dictionary of existing variable attributes
            config_var: Dictionary of configured variable attributes
        
        Returns:
            True if all configured attributes match the existing variable
        """
        # Ignore these keys when comparing
        ignore_keys = {'id', '_links', 'delete'}
        
        # Check if all configured attributes match existing variable
        for key, value in config_var.items():
            if key in ignore_keys:
                continue
            if key not in existing_var or existing_var[key] != value:
                return False
        return True

    def process_variables(
        self,
        group_or_project: Group | Project,
        configured_variables: Dict,
        enforce: bool,
    ):
        """Process variables configuration for a project or group.

        This method:
        1. Retrieves current variables from the project or group
        2. Processes configured variables (create/update/delete)
        3. Handles enforce mode if enabled (deletes unconfigured variables)
        4. Supports environment-scoped variables
        5. Supports all GitLab API variable attributes

        Args:
            group_or_project: Group or Project object
            configuration: Dictionary of variable configurations
            enforce: Boolean flag to enable or disable enforce mode
        """
        try:
            existing_variables = self.get_variables_from_gitlab(group_or_project)

            # Create lookup of existing variables considering all attributes
            existing_vars_lookup = {
                self._create_lookup_key(var.asdict()): var
                for var in existing_variables
            }

            verbose(f"Found {len(existing_variables)} existing variables in {group_or_project.name}")

            # Process all configured variables (both new and existing)
            processed_existing_vars = set()
            if configured_variables:
                verbose(f"Processing {len(configured_variables)} variables from configuration")
                # This will:
                # 1. Create any new variables defined in configuration
                # 2. Update any existing variables that need changes
                # 3. Track which existing variables were processed (for enforce mode)
                processed_existing_vars = self._process_configured_variables(
                    group_or_project, configured_variables, existing_vars_lookup
                )

            # Handle cleanup of unprocessed existing variables
            if enforce:
                vars_to_delete = len(existing_variables) - len(processed_existing_vars)
                if vars_to_delete > 0:
                    verbose(
                        f"Enforce mode will delete {vars_to_delete} existing variables "
                        f"that were not in configuration from {group_or_project.name}"
                    )
                self._delete_unconfigured_variables(existing_variables, processed_existing_vars)

        except Exception as err:
            warning(f"Failed to process variables for {group_or_project.name}: {str(err)}")
            raise

    def _process_configured_variables(
        self,
        group_or_project: Group | Project,
        configured_variables: Dict[str, Any],
        current_vars_lookup: Dict[Tuple[str, str], GroupVariable | ProjectVariable],
    ) -> Set[Tuple[str, str]]:
        """Process all variables defined in the configuration.

        This method:
        1. Iterates through each variable in the configuration
        2. Processes all attributes defined in the configuration
        3. Tracks each variable being processed, including those marked for deletion
        4. Calls _handle_variable to perform the actual operation (create/update/delete)

        Args:
            group_or_project: GitLab group or project object
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
            # Create lookup key using key and scope
            lookup_key = self._create_lookup_key(var_config, is_config=True)
            processed_vars.add(lookup_key)

            # Handle the variable with all its configured attributes
            self._handle_variable(group_or_project, var_config, current_vars_lookup)

        return processed_vars

    def _handle_variable(
        self,
        group_or_project: Group | Project,
        var_config: Dict[str, Any],
        current_vars_lookup: Dict[Tuple[str, str], GroupVariable | ProjectVariable],
    ) -> None:
        """Handle a single variable: create, update, or delete."""
        key: str = var_config["key"]
        env_scope: str = var_config.get("environment_scope", "*")
        should_delete: bool = var_config.get("delete", False)

        # Look up existing variable using key and scope
        lookup_key = self._create_lookup_key(var_config)
        existing_var = current_vars_lookup.get(lookup_key)

        if existing_var:
            existing_attrs = existing_var.asdict()
            
            # For delete operations, verify all provided attributes match
            if should_delete:
                if not self._variables_match(existing_attrs, var_config):
                    error_msg = (f"Cannot delete variable {key} with scope {env_scope} - "
                               "provided attributes don't match existing variable")
                    # fatal(error_msg)
                    raise Exception(error_msg)

                verbose(f"Deleting variable {key} with scope {env_scope}")
                group_or_project.variables.delete(key, filter={"environment_scope": env_scope})
            elif not self._variables_match(existing_attrs, var_config):
                # Update if attributes don't match
                verbose(f"Updating variable {key} with scope {env_scope}")
                variable_attributes = var_config.copy()
                variable_attributes.pop("delete", None)
                group_or_project.variables.update(
                    key,
                    variable_attributes,
                    filter={"environment_scope": env_scope},
                )
        else:
            if should_delete:
                verbose(f"Cannot delete variable {key} with scope {env_scope}, as it does not exist")
                raise Exception(
                    "To delete a variable with scope, make sure to specify 'environment_scope' in the config"
                )
            else:
                verbose(f"Creating new variable {key} with scope {env_scope}")
                variable_attributes = var_config.copy()
                variable_attributes.pop("delete", None)
                group_or_project.variables.create(variable_attributes)

    def _delete_unconfigured_variables(
        self,
        current_variables: List[GroupVariable] | List[ProjectVariable],
        processed_vars: Set[Tuple[Tuple[str, Any], ...]],
    ) -> None:
        """Delete variables that are not in the configuration when enforce mode is enabled."""
        for var in current_variables:
            lookup_key = self._create_lookup_key(var.asdict())
            if lookup_key not in processed_vars:
                verbose(f"Deleting variable {var.key} with scope {getattr(var, 'environment_scope', '*')}")
                var.delete(filter={"environment_scope": getattr(var, "environment_scope", "*")})
