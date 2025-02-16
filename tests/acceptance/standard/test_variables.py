import pytest
from gitlab import GitlabGetError, GitlabListError

from tests.acceptance import run_gitlabform


class TestVariables:
    """Test suite for GitLab project variable operations.

    Tests variable creation, updates, deletion, and environment-scoped variables
    using gitlabform configuration.
    """

    @pytest.mark.skip(
        reason=(
            "GitLab API behaviour changed in version 17.7.0."
            " Disable this test until more clarification is available."
            " Track this issue in GitLab at https://gitlab.com/gitlab-org/gitlab/-/issues/511237"
        )
    )
    def test__builds_disabled(self, project_for_function):
        config_builds_not_enabled = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            project_settings:
              builds_access_level: disabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_builds_not_enabled, project_for_function)

        with pytest.raises(GitlabListError):
            # variables will NOT be available without builds_access_level in ['private', 'enabled']
            vars = project_for_function.variables.list()
            print("vars: ", type(vars), vars)

    @pytest.mark.parametrize(
        "initial_vars, config_vars, expected",
        [
            # Test case 1: Single variable - no change
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123"}],
                [("FOO", "123")],
            ),
            # Test case 2: Single variable - update
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123456"}],
                [("FOO", "123456")],
            ),
            # Test case 3: Single variable - delete
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123", "delete": True}],
                [("FOO", None)],
            ),
            # Test case 4: Multiple variables - all operations
            (
                [
                    {"key": "FOO", "value": "123"},  # will be updated
                    {"key": "BAR", "value": "bleble"},  # will be deleted
                    {"key": "BAZ", "value": "old"},  # will stay the same
                ],
                [
                    {"key": "FOO", "value": "123456"},  # update
                    {"key": "BAR", "value": "bleble", "delete": True},  # delete
                    {"key": "BAZ", "value": "old"},  # no change
                    {"key": "QUX", "value": "new"},  # create new
                ],
                [
                    ("FOO", "123456"),  # updated
                    ("BAR", None),  # deleted
                    ("BAZ", "old"),  # unchanged
                    ("QUX", "new"),  # newly created
                ],
            ),
            # Test case 5: Single variable with multiple scopes
            (
                [
                    {
                        "key": "FOO",
                        "value": "prod-val",
                        "environment_scope": "prod",
                    },  # will be updated
                    {
                        "key": "FOO",
                        "value": "stage-val",
                        "environment_scope": "stage",
                    },  # will be deleted
                    {
                        "key": "FOO",
                        "value": "dev-val",
                        "environment_scope": "dev",
                    },  # will stay same
                ],
                [
                    {
                        "key": "FOO",
                        "value": "new-prod",
                        "environment_scope": "prod",
                    },  # update
                    {
                        "key": "FOO",
                        "value": "stage-val",
                        "environment_scope": "stage",
                        "delete": True,
                    },  # delete
                    {
                        "key": "FOO",
                        "value": "dev-val",
                        "environment_scope": "dev",
                    },  # no change
                    {
                        "key": "FOO",
                        "value": "test-val",
                        "environment_scope": "test",
                    },  # create new
                ],
                [
                    ("FOO", "new-prod", "prod"),  # updated
                    ("FOO", None, "stage"),  # deleted
                    ("FOO", "dev-val", "dev"),  # unchanged
                    ("FOO", "test-val", "test"),  # newly created
                ],
            ),
            # Test case 6: Multiple variables with multiple scopes
            (
                [
                    {
                        "key": "DB_URL",
                        "value": "prod-db",
                        "environment_scope": "prod",
                    },  # will be updated
                    {
                        "key": "DB_URL",
                        "value": "stage-db",
                        "environment_scope": "stage",
                    },  # will be deleted
                    {
                        "key": "API_KEY",
                        "value": "prod-key",
                        "environment_scope": "prod",
                    },  # will stay same
                    {
                        "key": "API_KEY",
                        "value": "stage-key",
                        "environment_scope": "stage",
                    },  # will be updated
                ],
                [
                    {
                        "key": "DB_URL",
                        "value": "new-prod-db",
                        "environment_scope": "prod",
                    },  # update
                    {
                        "key": "DB_URL",
                        "value": "stage-db",
                        "environment_scope": "stage",
                        "delete": True,
                    },  # delete
                    {
                        "key": "DB_URL",
                        "value": "dev-db",
                        "environment_scope": "dev",
                    },  # create new
                    {
                        "key": "API_KEY",
                        "value": "prod-key",
                        "environment_scope": "prod",
                    },  # no change
                    {
                        "key": "API_KEY",
                        "value": "new-stage-key",
                        "environment_scope": "stage",
                    },  # update
                    {
                        "key": "API_KEY",
                        "value": "test-key",
                        "environment_scope": "test",
                    },  # create new
                ],
                [
                    ("DB_URL", "new-prod-db", "prod"),  # updated
                    ("DB_URL", None, "stage"),  # deleted
                    ("DB_URL", "dev-db", "dev"),  # newly created
                    ("API_KEY", "prod-key", "prod"),  # unchanged
                    ("API_KEY", "new-stage-key", "stage"),  # updated
                    ("API_KEY", "test-key", "test"),  # newly created
                ],
            ),
            # Test case 7: Enforce mode - delete unspecified variables
            (
                [
                    {"key": "FOO", "value": "123"},  # will stay
                    {"key": "BAR", "value": "456"},  # will be deleted
                    {"key": "BAZ", "value": "789"},  # will be deleted
                ],
                {
                    "enforce": True,
                    "foo": {"key": "FOO", "value": "123"},  # only keep this one
                },
                [("FOO", "123")],  # BAR and BAZ are deleted
            ),
            
            # Test case 8: Enforce mode - with updates and new variables
            (
                [
                    {"key": "FOO", "value": "123"},  # will be updated
                    {"key": "BAR", "value": "456"},  # will be deleted
                ],
                {
                    "enforce": True,
                    "foo": {"key": "FOO", "value": "new123"},  # update this
                    "baz": {"key": "BAZ", "value": "789"},     # create this
                },
                [
                    ("FOO", "new123"),  # updated
                    ("BAZ", "789"),     # newly created
                ],  # BAR is deleted
            ),
            
            # Test case 9: Enforce mode - with environment scopes
            (
                [
                    {"key": "FOO", "value": "prod-val", "environment_scope": "prod"},  # will stay
                    {"key": "FOO", "value": "stage-val", "environment_scope": "stage"},  # will be deleted
                    {"key": "BAR", "value": "test-val", "environment_scope": "test"},  # will be deleted
                ],
                {
                    "enforce": True,
                    "foo_prod": {
                        "key": "FOO",
                        "value": "prod-val",
                        "environment_scope": "prod",
                    },  # keep this
                },
                [("FOO", "prod-val", "prod")],  # only prod scope remains
            ),
            
            # Test case 10: Enforce mode - multiple variables with multiple scopes
            (
                [
                    {"key": "DB_URL", "value": "prod-db", "environment_scope": "prod"},    # will stay
                    {"key": "DB_URL", "value": "stage-db", "environment_scope": "stage"},  # will be deleted
                    {"key": "API_KEY", "value": "prod-key", "environment_scope": "prod"},  # will stay
                    {"key": "API_KEY", "value": "stage-key", "environment_scope": "stage"},  # will be updated
                    {"key": "SECRET", "value": "123", "environment_scope": "prod"},        # will be deleted
                ],
                {
                    "enforce": True,
                    "db_url_prod": {
                        "key": "DB_URL",
                        "value": "prod-db",
                        "environment_scope": "prod",
                    },  # keep this
                    "api_key_prod": {
                        "key": "API_KEY",
                        "value": "prod-key",
                        "environment_scope": "prod",
                    },  # keep this
                    "api_key_stage": {
                        "key": "API_KEY",
                        "value": "new-stage-key",
                        "environment_scope": "stage",
                    },  # update this
                },
                [
                    ("DB_URL", "prod-db", "prod"),          # unchanged
                    ("API_KEY", "prod-key", "prod"),        # unchanged
                    ("API_KEY", "new-stage-key", "stage"),  # updated
                ],  # DB_URL stage and SECRET prod are deleted
            ),
        ],
        ids=[
            "test_case_1_single_var_no_change",
            "test_case_2_single_var_update",
            "test_case_3_single_var_delete",
            "test_case_4_multiple_vars_all_operations",
            "test_case_5_single_var_multiple_scopes",
            "test_case_6_multiple_vars_multiple_scopes",
            "test_case_7_enforce_mode_delete_unspecified",
            "test_case_8_enforce_mode_with_updates_and_new",
            "test_case_9_enforce_mode_with_environment_scopes",
            "test_case_10_enforce_mode_multiple_vars_multiple_scopes",
        ],
    )
    def test__variables(
        self, project_for_function, initial_vars, config_vars, expected
    ):
        """Test variable operations using gitlabform.

        Args:
            project_for_function: GitLab project fixture
            initial_vars: List of variables to create initially using GitLab API
            config_vars: List of variables to configure using gitlabform
            expected: List of (key, value) or (key, value, scope) tuples
                     value is None for variables that should be deleted
        """
        # Set initial variables
        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = self._create_config(project_for_function, config_vars)
        run_gitlabform(config, project_for_function)

        # Verify results
        for expected_var in expected:
            key, value, *env_scope = expected_var
            get_params = (
                {"filter": {"environment_scope": env_scope[0]}} if env_scope else {}
            )

            if value is None:
                with pytest.raises(GitlabGetError):
                    project_for_function.variables.get(key, **get_params)
            else:
                variable = project_for_function.variables.get(key, **get_params)
                assert variable.value == value

    def _create_config(self, project_for_function, variables):
        """Creates YAML configuration for GitLab project variables.

        Args:
            project_for_function: GitLab project instance
            variables: Dictionary with variable configurations and optional enforce mode
                      or List of variable configurations

        Returns:
            str: YAML configuration string

        Example YAML structure:
            projects_and_groups:
              project_path:
                project_settings:
                  builds_access_level: enabled
                variables:
                  enforce: true  # Optional. If true, deletes variables not in config
                  var_name:
                    key: VAR_NAME
                    value: var_value
                    [environment_scope: scope]
                    [filter[environment_scope]: scope]
                    [delete: true]
        """
        # Main configuration template
        template = """\
projects_and_groups:
  {project}:
    project_settings:
      builds_access_level: enabled
    variables:
{variables}"""

        # Variable entry template
        var_template = """\
      {name}:
        key: {key}
        value: {value}{env_scope}{delete}"""

        # Environment scope template
        env_scope_template = """\
        environment_scope: {scope}
        filter[environment_scope]: {scope}"""

        # Delete flag template
        delete_template = """\
        delete: true"""

        # Enforce mode template
        enforce_template = """\
      enforce: true"""

        # Build variables section
        var_configs = []

        # Handle enforce mode
        if isinstance(variables, dict) and "enforce" in variables:
            var_configs.append(enforce_template)
            # Extract the variable configurations, excluding 'enforce'
            var_list = [variables[k] for k in variables if k != "enforce"]
        else:
            var_list = variables

        # Process each variable
        for var in var_list:
            # Create unique name for variable (including scope if present)
            name = var["key"].lower()
            if "environment_scope" in var:
                name = f"{name}_{var['environment_scope'].replace('/', '_')}"

            # Add environment scope config if present
            env_scope = ""
            if "environment_scope" in var:
                env_scope = "\n" + env_scope_template.format(
                    scope=var["environment_scope"]
                )

            # Add delete flag if present
            delete = "\n" + delete_template if var.get("delete") else ""

            # Format variable config
            var_config = var_template.format(
                name=name,
                key=var["key"],
                value=var["value"],
                env_scope=env_scope,
                delete=delete,
            )
            var_configs.append(var_config)

        # Combine all configs
        return template.format(
            project=project_for_function.path_with_namespace,
            variables="\n".join(var_configs),
        )
