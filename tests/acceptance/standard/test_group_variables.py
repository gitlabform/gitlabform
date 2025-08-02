from unittest.mock import patch
import pytest
from tests.acceptance import run_gitlabform
from cli_ui import debug as verbose  # for wraps


class TestGroupVariables:
    """Test suite for GitLab group variable operations.

    Tests variable creation, updates, deletion using gitlabform configuration.
    """

    def test__add_new_variables(self, group):
        """Test case: add new variables, including special characters and complex values"""

        # Set initial variables
        initial_vars = [
            {"key": "FOO", "value": "foo123"},
        ]

        for var in initial_vars:
            group.variables.create(var)

        # Verify that 1 initial variable have been set
        assert len(group.variables.list(get_all=True)) == 1

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
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
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 4

        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"

        assert variables[1].key == "BAR"
        assert variables[1].value == "bar-value"

        assert variables[2].key == "SPECIAL_CHARS"
        assert variables[2].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"

        assert variables[3].key == "COMPLEX_VALUE"
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
        assert variables[3].value == expected_message

    @patch("gitlabform.processors.util.variables_processor.verbose", wraps=verbose)
    def test__update_variables(self, mock_verbose, group):
        """Test case: update variables that were added in previous test case"""

        # Verify that 4 initial variables have been set because 'group' is class scoped fixture and the last test case result will set 3 variables.
        assert len(group.variables.list(get_all=True)) == 4

        # Test1: Variable update should not be attempted if there are no changes
        config_no_change = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              FOO_variable:
                key: FOO
                value: foo123
        """
        # Import after verbose patch is applied by the function decorator.
        # This will be usd for capturing verbose logs by the module to verify
        # that variable update is not attempted
        from gitlabform.processors.util.variables_processor import VariablesProcessor

        run_gitlabform(config_no_change, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 4

        # Check verbose log output
        actual_messages = [call.args[0] for call in mock_verbose.call_args_list]

        expected_messages = [
            "Variable FOO with scope * already matches configuration, no update needed",
        ]

        for expected in expected_messages:
            assert any(expected in msg for msg in actual_messages), f"Missing verbose: {expected}"

        # Expect 'FOO' variables to remain unchanged because it was not in the config
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        # Test2: Variable update should happen
        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              # Not configuring 'FOO' variable with default scope. Expect that to remain as-is
              BAR_variable:
                key: BAR
                value: bar-value-updated
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 4

        # Expect 'FOO' variable with default scope to remain unchanged because it was not in the config
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"

        assert variables[1].key == "BAR"
        assert variables[1].value == "bar-value-updated"

        assert variables[2].key == "SPECIAL_CHARS"
        assert variables[2].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"

        assert variables[3].key == "COMPLEX_VALUE"
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
        assert variables[3].value == expected_message

    def test__delete_variables(self, group, capsys):
        """Test case: Variable deletion scenarios"""

        # Clear any existing variables from previous tests since 'group' is class-scoped
        existing = group.variables.list(get_all=True)
        for var in existing:
            group.variables.delete(var.key, filter={"environment_scope": var.environment_scope})

        # Set initial variables for all test scenarios
        initial_vars = [
            {"key": "KEY_ONLY", "value": "value123"},  # for key-only delete
            {"key": "KEY_VALUE", "value": "match-this"},  # for key-value match delete
            {"key": "WRONG_VALUE", "value": "actual-value"},  # for wrong value test
            {  # for attribute match tests
                "key": "MULTI_ATTR",
                "value": "test-xyz-123",
                "protected": True,
                "masked": True,
                "variable_type": "env_var",
            },
        ]
        for var in initial_vars:
            group.variables.create(var)

        # Verify initial state
        assert len(group.variables.list(get_all=True)) == 4

        # Test 1: Delete with key only
        config_key_only = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              key_only_var:
                key: KEY_ONLY
                delete: true
        """
        run_gitlabform(config_key_only, group)
        variables = group.variables.list(get_all=True)
        assert len(variables) == 3
        assert not any(v.key == "KEY_ONLY" for v in variables)

        # Test 2: Delete with key and value match
        config_key_value = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              key_value_var:
                key: KEY_VALUE
                value: match-this
                delete: true
        """
        run_gitlabform(config_key_value, group)
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2
        assert not any(v.key == "KEY_VALUE" for v in variables)

        # Test 3: Delete should fail with wrong value
        config_wrong_value = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              wrong_value_var:
                key: WRONG_VALUE
                value: wrong-value
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_wrong_value, group)
        captured = capsys.readouterr()
        assert "Cannot delete WRONG_VALUE - attributes don't match" in captured.err

        # Test 4: Delete should fail for non-existent variable
        config_non_existent = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              non_existent_var:
                key: NON_EXISTENT
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_non_existent, group)
        captured = capsys.readouterr()
        assert "Cannot delete variable 'NON_EXISTENT' with scope '*' - variable does not exist" in captured.err

        # Test 5: Delete should fail when specified attributes don't match
        config_mismatch = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              multi_attr_var:
                key: MULTI_ATTR
                value: test-xyz-123     # match
                protected: False        # doesn't match
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_mismatch, group)
        captured = capsys.readouterr()
        assert "Cannot delete MULTI_ATTR - attributes don't match" in captured.err

        # Test 6: Delete should succeed when providing subset of attributes
        config_partial = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              multi_attr_var:
                key: MULTI_ATTR
                value: test-xyz-123     # match
                protected: True         # match
                # masked is not specified (should not affect matching)
                # variable_type is not specified (should not affect matching)
                delete: true
        """
        run_gitlabform(config_partial, group)
        variables = group.variables.list(get_all=True)
        assert len(variables) == 1  # Only WRONG_VALUE variable should remain
        assert not any(v.key == "MULTI_ATTR" for v in variables)

    def test__raw_parameter_passing(self, group):
        """Test case: validate raw parameter passing design works by setting extra optional attributes for variables"""

        # The previous test case using 'group' fixture ends with 2 variables.
        variables = group.variables.list(get_all=True)
        assert len(variables) == 1  # Only WRONG_VALUE variable should remain

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              FOO_variable:
                description: this is a prod scoped protected and masked variable
                key: FOO
                value: foo-123-xyz  # value must follow masking requirement
                protected: true
                masked: true
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        assert variables[1].description == "this is a prod scoped protected and masked variable"
        assert variables[1].key == "FOO"
        assert variables[1].value == "foo-123-xyz"
        assert variables[1].protected is True
        assert variables[1].masked is True

    def test__preserve_unconfigured_attributes(self, group):
        """Test case: When updating a variable, any attributes that is not in config, should remain as-is"""

        # The previous test case using 'group' fixture ends with 2 variables.
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              FOO_variable:
                key: FOO
                value: foo-123-xyz-new-value  # value must follow masking requirement as previously it was configured
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        # Expect the variable to be updated, but other attributes like description, protected, masked should remain unchanged
        # because they were not specified in the config.
        # This tests the design of preserving unconfigured attributes.
        # The description, protected, and masked attributes should remain as they were set in the previous
        # test case. The value should be updated to the new value specified in the config.
        assert variables[1].description == "this is a prod scoped protected and masked variable"
        assert variables[1].key == "FOO"
        assert variables[1].value == "foo-123-xyz-new-value"
        assert variables[1].protected is True
        assert variables[1].masked is True

    def test__enforce_mode_delete_all_variables(self, group):
        """Test case: Enforce mode - delete all variables"""

        # Initial variables should already be set for the 'group' because it's a class scoped fixture.
        # Ensure the group has correct number of variables from the latest state of previous test.
        assert len(group.variables.list(get_all=True)) == 2

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              enforce: true
        """
        run_gitlabform(config, group)

        # Verify results - all variables should be deleted
        variables = group.variables.list(get_all=True)
        assert len(variables) == 0

    def test__enforce_mode_with_all_operations(self, group):
        """Test case: Enforce mode - with all operations (i.e. add, delete, update)"""

        # Initial variables be empty for the 'group' because it's a class scoped fixture and previous test deleted all variables.
        assert len(group.variables.list(get_all=True)) == 0

        # Add some new variables so that we can test gitlabform config
        initial_vars = [
            # A new variable will be added using gitlabform
            {"key": "FOO1", "value": "123"},  # should not change because gitlabform config will be same
            {"key": "BAR", "value": "456"},  # should be updated because gitlabform config will apply new value
            {
                "key": "FOO2",
                "value": "value",
            },  # should be deleted because of ommission in gitlabform config and 'enforce' mode
            {"key": "BAZ", "value": "789"},  # should be deleted because gitlabform config will use the 'delete' key
        ]

        for var in initial_vars:
            group.variables.create(var)

        # Verify that 4 initial variables have been set
        assert len(group.variables.list(get_all=True)) == 4

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              enforce: true
              NEW_variable:
                key: NEW
                value: new-var-value
              FOO1_variable:
                key: FOO1
                value: 123
              BAR_variable:
                key: BAR
                value: 456_updated
              BAZ_variable:
                key: BAZ
                delete: true

        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 3
        assert variables[0].key == "FOO1"
        assert variables[0].value == "123"
        assert variables[1].key == "BAR"
        assert variables[1].value == "456_updated"
        assert variables[2].key == "NEW"
        assert variables[2].value == "new-var-value"
