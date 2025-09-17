import pytest
from gitlab.exceptions import GitlabListError
from gitlabform.constants import EXIT_PROCESSING_ERROR

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
    def test__builds_disabled(self, project):
        config_builds_not_enabled = f"""
        projects_and_groups:
          {self.project.path_with_namespace}:
            project_settings:
              builds_access_level: disabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_builds_not_enabled, project)

        with pytest.raises(GitlabListError):
            # variables will NOT be available without builds_access_level in ['private', 'enabled']
            vars = self.project.variables.list()
            print("vars: ", type(vars), vars)


    def test__single_variable_no_change(self, project_for_function):
        """Test case: Single variable - no change"""

        # Set initial variables
        initial_vars = [{"key": "FOO", "value": "123"}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              FOO:
                key: FOO
                value: 123
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "FOO"
        assert variables[0].value == "123"

    def test__single_variable_update(self, project_for_function):
        """Test case: Single variable - update"""

        # Set initial variables
        initial_vars = [{"key": "FOO", "value": "123"}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              FOO:
                key: FOO
                value: 123456
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "FOO"
        assert variables[0].value == "123456"

    def test__single_variable_delete(self, project_for_function):
        """Test case: Single variable - delete"""

        # Set initial variables
        initial_vars = [{"key": "FOO", "value": "123"}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              FOO:
                key: FOO
                value: 123456
                delete: true
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 0

    def test__single_variable_delete_using_variable_key_only(self, project_for_function):
        """Test case: Single variable - delete using variable key only"""

        # Set initial variables
        initial_vars = [{"key": "FOO", "value": "123"}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              FOO:
                key: FOO
                delete: true
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 0

    def test__multiple_variables_all_operations(self, project_for_function):
        """Test case: Multiple variables - all operations"""

        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "123"},  # will be updated
            {"key": "BAR", "value": "bleble"},  # will be deleted
            {"key": "BAZ", "value": "old"},  # will stay the same
            # A new variable will be added using gitlabform
        ]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              FOO:
                key: FOO
                value: 123456
              BAR:
                key: BAR
                delete: true
              BAZ:
                key: BAZ
                value: old
              QUX:
                key: QUX
                value: new
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 3
        assert variables[0].key == "FOO"
        assert variables[0].value == "123456"
        assert variables[1].key == "BAZ"
        assert variables[1].value == "old"
        assert variables[2].key == "QUX"
        assert variables[2].value == "new"

    def test__enforce_mode_delete_all_variables(self, project_for_function):
        """Test case: Enforce mode - delete all variables"""

        # Set initial variables
        initial_vars = [{"key": "FOO", "value": "123"}, {"key": "BAR", "value": "456"}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              enforce: true
        """
        run_gitlabform(config, project_for_function)

        # Verify results - all variables should be deleted
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 0

    def test__enforce_mode_with_all_operations(self, project_for_function):
        """Test case: Enforce mode - with all operations (i.e. add, delete, update)"""
        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "123"},  # will stay
            {"key": "BAR", "value": "456"},  # will be updated
            {"key": "BAZ", "value": "789"},  # will be deleted via delete key
            {
                "key": "BLAH",
                "value": "blahblah",
            },  # will be deleted because of ommission in gitlabform config and 'enforce' mode
            # A new variable will be added using gitlabform
        ]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Verify that 4 initial variables have been set
        assert len(project_for_function.variables.list(get_all=True)) == 4

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              enforce: true
              FOO:
                key: FOO
                value: 123
              BAR:
                key: BAR
                value: 456_updated
              BAZ:
                key: BAZ
                delete: true
              QUX:
                key: QUX
                value: new 
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 3
        assert variables[0].key == "FOO"
        assert variables[0].value == "123"
        assert variables[1].key == "BAR"
        assert variables[1].value == "456_updated"
        assert variables[2].key == "QUX"
        assert variables[2].value == "new"

    def test__raw_params_passed(self, project_for_function):
        """Test case: Raw parameters (protected, masked)"""
        # Set initial variables
        initial_vars = []  # no initial vars

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              Protected_variable:
                key: PROTECTED_VAR
                value: secret123
                protected: true
                masked: true
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "PROTECTED_VAR"
        assert variables[0].value == "secret123"
        assert variables[0].protected is True
        assert variables[0].masked is True

    def test__preserve_protected_status(self, project_for_function):
        """Test case: Preserve protected status on update if protected config is not set"""
        # Set initial variables
        initial_vars = [{"key": "PROTECTED_VAR", "value": "secret123", "protected": True}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              Protected_variable:
                key: PROTECTED_VAR
                value: newvalue
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "PROTECTED_VAR"
        assert variables[0].value == "newvalue"
        assert variables[0].protected is True

    def test__preserve_masked_status(self, project_for_function):
        """Test case: Preserve masked status on update if masked config is not set"""
        # Set initial variables
        initial_vars = [{"key": "MASKED_VAR", "value": "secret123", "masked": True}]

        for var in initial_vars:
            project_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              Masked_variable:
                key: MASKED_VAR
                value: newvalue
        """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "MASKED_VAR"
        assert variables[0].value == "newvalue"
        assert variables[0].masked is True

    def test__special_characters(self, project_for_function):
        """Test case: Special characters in value"""

        # Apply gitlabform config
        config = f"""
            projects_and_groups:
              {project_for_function.path_with_namespace}:
                variables:
                  Variable_value_with_special_chars:
                    key: SPECIAL_CHARS
                    value: "!@#$%^&*()_+-=[]{{}}|;:,.<>?"
            """
        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "SPECIAL_CHARS"
        assert variables[0].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def test__complex_yaml_config(self, project_for_function):
        """Test case: Complex YAML configuration handling"""

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            variables:
              Variable_value_with_special_chars:
                key: CONFIG_WITH_SPECIAL
                value: |
                  # This represents a typical complex configuration value
                  host: ${{HOST_VAR}}
                  port: 8080
                  paths:
                    - /api/v1
                    - /api/v2
        """

        run_gitlabform(config, project_for_function)

        # Verify results
        variables = project_for_function.variables.list(get_all=True)
        assert len(variables) == 1
        assert variables[0].key == "CONFIG_WITH_SPECIAL"
        # The \n is needed because the value is a multi-line string.
        # Each line break in the YAML block literal (|) is preserved as a newline character in the string.
        # Without the \n, all lines would be concatenated together, which does not match the actual value.
        # To debug, print the value to see the actual string:
        assert variables[0].value == (
            "# This represents a typical complex configuration value\n"
            "host: ${HOST_VAR}\n"
            "port: 8080\n"
            "paths:\n"
            "  - /api/v1\n"
            "  - /api/v2\n"
        )

    def test__delete_variables_scope_requires_specifying_scope(self, group_for_function, capsys):
        """Test case: If a variable is configured with non-default environment scope,
        deleting will require specifying the environment scope in gitlabform config."""
        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "prod-val", "environment_scope": "prod"},  # will be deleted
        ]

        error_message_for_delete_without_scope = (
            "To delete a variable with scope, make sure to specify 'environment_scope' in the config"
        )

        for var in initial_vars:
            group_for_function.variables.create(var)

        # Ensure 1 initial variables have been configured
        assert len(group_for_function.variables.list(get_all=True)) == 1

        # Test using wrong config
        config_wrong = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo_prod:
                key: FOO
                delete: true
        """

        # Verify results
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_wrong, group_for_function)

        captured_output = capsys.readouterr()

        assert exc_info.value.code == 2
        assert exc_info.type == SystemExit
        assert exc_info.value.code == EXIT_PROCESSING_ERROR
        assert error_message_for_delete_without_scope in captured_output.err

        variables = group_for_function.variables.list(get_all=True)
        assert len(variables) == 1  # variable wasn't deleted due to config error

        # Now test using correct config
        config_correct = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo_prod:
                key: FOO
                environment_scope: prod
                delete: true
        """
        run_gitlabform(config_correct, group_for_function)

        # Verify results
        variables = group_for_function.variables.list(get_all=True)
        assert len(variables) == 0

    def test__variables_same_key_different_scopes(self, group_for_function):
        """Test case: Variable with same key but different scopes"""
        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "prod-val", "environment_scope": "prod"},  # value will be updated
            {"key": "FOO", "value": "stage-val", "environment_scope": "stage"},  # will be deleted using 'delete' key
            {"key": "FOO", "value": "dev-val", "environment_scope": "dev"},  # protected will be set
            # A new variable will be added using gitlabform
        ]

        for var in initial_vars:
            group_for_function.variables.create(var)

        # Ensure 3 initial variables have been configured
        assert len(group_for_function.variables.list(get_all=True)) == 3

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo_prod:
                key: FOO
                value: new-prod-value
                environment_scope: prod
              foo_stage:
                key: FOO
                environment_scope: stage
                delete: true
              foo_dev:
                key: FOO
                value: dev-val
                environment_scope: dev
                protected: true
              foo_test:
                key: FOO
                value: test-val
                environment_scope: test
        """
        run_gitlabform(config, group_for_function)

        # Verify results
        variables = group_for_function.variables.list(get_all=True)
        assert len(variables) == 3

        assert variables[0].key == "FOO"
        assert variables[0].value == "new-prod-value"
        assert variables[0].environment_scope == "prod"

        assert variables[1].key == "FOO"
        assert variables[1].value == "dev-val"
        assert variables[1].environment_scope == "dev"
        assert variables[1].protected is True

        assert variables[2].key == "FOO"
        assert variables[2].value == "test-val"
        assert variables[2].environment_scope == "test"

    def test__enforce_mode_with_environment_scopes(self, group_for_function):
        """Test case: Enforce mode with environment scopes"""
        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "prod-val", "environment_scope": "prod"},  # value will be updated
            {
                "key": "FOO",
                "value": "stage-val",
                "environment_scope": "stage",
            },  # ommitted in gitlabform config - will be deleted due to 'enforce' mode
        ]

        for var in initial_vars:
            group_for_function.variables.create(var)

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              enforce: true
              foo_prod:
                key: FOO
                value: prod-new-val
                environment_scope: prod
        """
        run_gitlabform(config, group_for_function)

        # Verify results
        variables = group_for_function.variables.list(get_all=True)
        assert len(variables) == 1

        assert variables[0].key == "FOO"
        assert variables[0].value == "prod-new-val"
        assert variables[0].environment_scope == "prod"
