import pytest
from cli_ui import debug as verbose  # for wraps
from unittest.mock import patch
from gitlab.exceptions import GitlabListError

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

    def test__add_new_variables(self, project):
        """Test case: add new variables, including special characters and complex values"""

        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "foo123"},
        ]

        for var in initial_vars:
            project.variables.create(var)

        # Verify that 1 initial variable have been set
        assert len(project.variables.list(get_all=True)) == 1

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              FOO_scoped_variable:
                key: FOO
                value: prod-value
                environment_scope: prod
              BAR_variable:
                key: BAR
                value: bar-value
              Special_chars_variable:
                key: SPECIAL_CHARS
                value: "!@#$%^&*()_+-=[]{{}}|;:,.<>?"
              Complex_value_variable:
                key: COMPLEX_VALUE
                value: |
                  # This represents a typical complex configuration value
                  host: ${{HOST_VAR}}
                  port: 8080
                  paths:
                    - /api/v1
                    - /api/v2
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 5

        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-value"
        assert variables[1].environment_scope == "prod"

        assert variables[2].key == "BAR"
        assert variables[2].value == "bar-value"
        assert variables[2].environment_scope == "*"  # default scope if not configured

        assert variables[3].key == "SPECIAL_CHARS"
        assert variables[3].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert variables[3].environment_scope == "*"  # default scope if not configured

        assert variables[4].key == "COMPLEX_VALUE"
        # The \n is needed because the value is a multi-line string.
        # Each line break in the YAML block literal (|) is preserved as a newline character in the string.
        # Without the \n, all lines would be concatenated together, which does not match the actual value.
        # To debug, print the value to see the actual string:
        expected_message = (
            "# This represents a typical complex configuration value\n"
            "host: ${HOST_VAR}\n"
            "port: 8080\n"
            "paths:\n"
            "  - /api/v1\n"
            "  - /api/v2\n"
        )
        assert variables[4].value == expected_message
        assert variables[4].environment_scope == "*"  # default scope if not configured

    @patch("gitlabform.processors.util.variables_processor.verbose", wraps=verbose)
    def test__update_variables(self, mock_verbose, project):
        """Test case: update variables that were added in previous test case"""

        # Verify that 5 initial variables have been set because 'project' is class scoped fixture and the last test case result will set 3 variables.
        assert len(project.variables.list(get_all=True)) == 5

        # Test1: Variable update should not be attempted if there are no changes
        config_no_change = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              FOO_variable:
                key: FOO
                value: foo123
              FOO_scoped_variable:
                key: FOO
                value: prod-value
                environment_scope: prod
        """
        # Import after verbose patch is applied by the function decorator.
        # This will be usd for capturing verbose logs by the module to verify
        # that variable update is not attempted
        from gitlabform.processors.util.variables_processor import VariablesProcessor

        run_gitlabform(config_no_change, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 5

        # Check verbose log output
        actual_messages = [call.args[0] for call in mock_verbose.call_args_list]

        expected_messages = [
            "Variable FOO with scope * already matches configuration, no update needed",
            "Variable FOO with scope prod already matches configuration, no update needed",
        ]

        for expected in expected_messages:
            assert any(expected in msg for msg in actual_messages), f"Missing verbose: {expected}"

        # Expect 'FOO' variables to remain unchanged because it was not in the config
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured
        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-value"
        assert variables[1].environment_scope == "prod"

        # Test2: Variable update should happen
        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              # Not configuring 'FOO' variable with default scope. Expect that to remain as-is
              FOO_scoped_variable:
                key: FOO
                value: prod-new-value
                environment_scope: prod
              BAR_variable:
                key: BAR
                value: bar-value-updated
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 5

        # Expect 'FOO' variable with default scope to remain unchanged because it was not in the config
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-new-value"
        assert variables[1].environment_scope == "prod"

        assert variables[2].key == "BAR"
        assert variables[2].value == "bar-value-updated"
        assert variables[2].environment_scope == "*"  # default scope if not configured

        assert variables[3].key == "SPECIAL_CHARS"
        assert variables[3].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert variables[3].environment_scope == "*"  # default scope if not configured

        assert variables[4].key == "COMPLEX_VALUE"
        # The \n is needed because the value is a multi-line string.
        # Each line break in the YAML block literal (|) is preserved as a newline character in the string.
        # Without the \n, all lines would be concatenated together, which does not match the actual value.
        # To debug, print the value to see the actual string:
        expected_message = (
            "# This represents a typical complex configuration value\n"
            "host: ${HOST_VAR}\n"
            "port: 8080\n"
            "paths:\n"
            "  - /api/v1\n"
            "  - /api/v2\n"
        )
        assert variables[4].value == expected_message
        assert variables[4].environment_scope == "*"  # default scope if not configured

    def test__delete_variables(self, project, capsys):
        """Test case: Variable deletion scenarios"""

        # Clear any existing variables from previous tests since 'project' is class-scoped
        existing = project.variables.list(get_all=True)
        for var in existing:
            project.variables.delete(var.key, filter={"environment_scope": var.environment_scope})

        # Set initial variables for all test scenarios
        initial_vars = [
            {"key": "KEY_ONLY", "value": "value123"},  # for key-only delete
            {"key": "KEY_VALUE", "value": "match-this"},  # for key-value match delete
            {"key": "KEY_SCOPE", "value": "any", "environment_scope": "prod"},  # for key-scope match delete
            {"key": "WRONG_VALUE", "value": "actual-value"},  # for wrong value test
            {"key": "WRONG_SCOPE", "value": "value", "environment_scope": "prod"},  # for wrong scope test
            {  # for attribute match tests
                "key": "MULTI_ATTR",
                "value": "test-xyz-123",
                "protected": True,
                "masked": True,
                "variable_type": "env_var",
                "environment_scope": "prod",
            },
        ]
        for var in initial_vars:
            project.variables.create(var)

        # Verify initial state
        assert len(project.variables.list(get_all=True)) == 6

        # Test 1: Delete with key only (default scope)
        config_key_only = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              key_only_var:
                key: KEY_ONLY
                delete: true
        """
        run_gitlabform(config_key_only, project)
        variables = project.variables.list(get_all=True)
        assert len(variables) == 5
        assert not any(v.key == "KEY_ONLY" for v in variables)

        # Test 2: Delete with key and value match
        config_key_value = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              key_value_var:
                key: KEY_VALUE
                value: match-this
                delete: true
        """
        run_gitlabform(config_key_value, project)
        variables = project.variables.list(get_all=True)
        assert len(variables) == 4
        assert not any(v.key == "KEY_VALUE" for v in variables)

        # Test 3: Delete with key and scope match
        config_key_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              key_scope_var:
                key: KEY_SCOPE
                environment_scope: prod
                delete: true
        """
        run_gitlabform(config_key_scope, project)
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3
        assert not any(v.key == "KEY_SCOPE" for v in variables)

        # Test 4: Delete should fail with wrong value
        config_wrong_value = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              wrong_value_var:
                key: WRONG_VALUE
                value: wrong-value
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_wrong_value, project)
        captured = capsys.readouterr()
        assert "Cannot delete WRONG_VALUE - attributes don't match" in captured.err

        # Test 5: Delete should fail with wrong scope
        config_wrong_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              wrong_scope_var:
                key: WRONG_SCOPE
                environment_scope: dev  # wrong scope, actual is 'prod'
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_wrong_scope, project)
        captured = capsys.readouterr()
        assert "Cannot delete variable 'WRONG_SCOPE' with scope 'dev' - variable does not exist" in captured.err

        # Test 6: Delete should fail for non-existent variable
        config_non_existent = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              non_existent_var:
                key: NON_EXISTENT
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_non_existent, project)
        captured = capsys.readouterr()
        assert "Cannot delete variable 'NON_EXISTENT' with scope '*' - variable does not exist" in captured.err

        # Test 7: Delete should fail when specified attributes don't match
        config_mismatch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              multi_attr_var:
                key: MULTI_ATTR
                value: test-xyz-123     # match
                protected: False        # doesn't match
                environment_scope: prod # match
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_mismatch, project)
        captured = capsys.readouterr()
        assert "Cannot delete MULTI_ATTR - attributes don't match" in captured.err

        # Test 8: Delete should succeed when providing subset of attributes
        config_partial = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              multi_attr_var:
                key: MULTI_ATTR
                value: test-xyz-123     # match
                protected: True         # match
                # masked is not specified (should not affect matching)
                # variable_type is not specified (should not affect matching)
                environment_scope: prod # match
                delete: true
        """
        run_gitlabform(config_partial, project)
        variables = project.variables.list(get_all=True)
        assert len(variables) == 2  # Only WRONG_VALUE and WRONG_SCOPE should remain
        assert not any(v.key == "MULTI_ATTR" for v in variables)

        # Verify final state
        variables = project.variables.list(get_all=True)
        assert len(variables) == 2  # Only WRONG_VALUE and WRONG_SCOPE should remain

    def test__raw_parameter_passing(self, project):
        """Test case: validate raw parameter passing design works by setting extra optional attributes for variables"""

        # The previous test case using 'project' fixture ends with 2 variables.
        variables = project.variables.list(get_all=True)
        assert len(variables) == 2

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              FOO_scoped_variable:
                description: this is a prod scoped protected and masked variable
                key: FOO
                value: foo-123-xyz  # value must follow masking requirement
                protected: true
                masked: true
                environment_scope: prod
                filter[environment_scope]: prod
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3

        assert variables[2].description == "this is a prod scoped protected and masked variable"
        assert variables[2].key == "FOO"
        assert variables[2].value == "foo-123-xyz"
        assert variables[2].protected is True
        assert variables[2].masked is True
        assert variables[2].environment_scope == "prod"

    def test__preserve_unconfigured_attributes(self, project):
        """Test case: When updating a variable, any attributes that is not in config, should remain as-is"""

        # The previous test case using 'project' fixture ends with 3 variables.
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              FOO_scoped_variable:
                key: FOO
                value: foo-123-xyz-new-value  # value must follow masking requirement as previously it was configured
                environment_scope: prod
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3

        assert variables[2].description == "this is a prod scoped protected and masked variable"
        assert variables[2].key == "FOO"
        assert variables[2].value == "foo-123-xyz-new-value"
        assert variables[2].protected is True
        assert variables[2].masked is True
        assert variables[2].environment_scope == "prod"

    def test__enforce_mode_delete_all_variables(self, project):
        """Test case: Enforce mode - delete all variables"""

        # Initial variables should already be set for the 'project' because it's a class scoped fixture.
        # Ensure the project has correct number of variables from the latest state of previous test.
        assert len(project.variables.list(get_all=True)) == 3

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              enforce: true
        """
        run_gitlabform(config, project)

        # Verify results - all variables should be deleted
        variables = project.variables.list(get_all=True)
        assert len(variables) == 0

    def test__enforce_mode_with_all_operations(self, project):
        """Test case: Enforce mode - with all operations (i.e. add, delete, update)"""

        # Initial variables be empty for the 'project' because it's a class scoped fixture and previous test deleted all variables.
        assert len(project.variables.list(get_all=True)) == 0

        # Add some new variables so that we can test gitlabform config
        initial_vars = [
            {"key": "FOO", "value": "123"},  # should not change because gitlabform config will be same
            {
                "key": "FOO",
                "value": "prod-value",
                "environment_scope": "prod",
            },  # should be deleted because of ommission in gitlabform config and 'enforce' mode
            {"key": "BAR", "value": "456"},  # should be updated because gitlabform config will apply new value
            {"key": "BAZ", "value": "789"},  # should be deleted because gitlabform config will use the 'delete' key
            {
                "key": "BLAH",
                "value": "blahblah",
            },  # Should be deleted because of ommission in gitlabform config and 'enforce' mode
            # A new variable will be added using gitlabform
        ]

        for var in initial_vars:
            project.variables.create(var)

        # Verify that 4 initial variables have been set
        assert len(project.variables.list(get_all=True)) == 5

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              enforce: true
              FOO_variable:
                key: FOO
                value: 123
              BAR_variable:
                key: BAR
                value: 456_updated
              BAZ_variable:
                key: BAZ
                delete: true
              QUX_variable:
                key: QUX
                value: new 
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3
        assert variables[0].key == "FOO"
        assert variables[0].value == "123"
        assert variables[1].key == "BAR"
        assert variables[1].value == "456_updated"
        assert variables[2].key == "QUX"
        assert variables[2].value == "new"
