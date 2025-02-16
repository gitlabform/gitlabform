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
            # Single variable - testing create, update, delete
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123"}],
                [("FOO", "123")],
            ),
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123456"}],
                [("FOO", "123456")],
            ),
            (
                [{"key": "FOO", "value": "123"}],
                [{"key": "FOO", "value": "123", "delete": True}],
                None,
            ),
            # Multiple variables - testing create, update, and delete together
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
                    ("BAZ", "old"),  # unchanged
                    ("QUX", "new"),  # newly created
                ],
            ),
            # Environment scopes - testing variables with different environment scopes
            (
                [{"key": "FOO1", "value": "alfa", "environment_scope": "test/ee"}],
                [{"key": "FOO1", "value": "alfa", "environment_scope": "test/ee"}],
                [("FOO1", "alfa", "test/ee")],
            ),
            (
                [
                    {"key": "FOO2", "value": "alfa", "environment_scope": "test/ee"},
                    {"key": "FOO2", "value": "beta", "environment_scope": "test/lv"},
                ],
                [
                    {"key": "FOO2", "value": "alfa", "environment_scope": "test/ee"},
                    {"key": "FOO2", "value": "beta", "environment_scope": "test/lv"},
                ],
                [("FOO2", "alfa", "test/ee"), ("FOO2", "beta", "test/lv")],
            ),
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
            expected: Expected state after gitlabform execution
                     None for deletion tests
                     List of (key, value) or (key, value, scope) tuples for other tests
        """
        # Set initial variables
        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = self._create_config(project_for_function, config_vars)
        run_gitlabform(config, project_for_function)

        # Verify results
        if expected is None:
            with pytest.raises(GitlabGetError):
                project_for_function.variables.get(config_vars[0]["key"])
            return

        for expected_var in expected:
            key, value, *env_scope = expected_var
            get_params = (
                {"filter": {"environment_scope": env_scope[0]}} if env_scope else {}
            )
            variable = project_for_function.variables.get(key, **get_params)
            assert variable.value == value

    def _create_config(self, project_for_function, variables):
        """Creates YAML configuration for GitLab project variables.

        Generates a YAML configuration string for gitlabform that defines project
        variables with their properties. Supports regular variables, environment-scoped
        variables, and variable deletion.

        Args:
            project_for_function: GitLab project instance
            variables: List of variable configurations, each containing:
                - key: Variable name
                - value: Variable value
                - environment_scope: Optional environment scope
                - delete: Optional deletion flag

        Returns:
            str: YAML configuration string

        Example YAML structure:
            projects_and_groups:
              project_path:
                project_settings:
                  builds_access_level: enabled
                variables:
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

        # Build variables section
        var_configs = []
        for var in variables:
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
