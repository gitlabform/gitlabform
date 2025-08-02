import pytest

from tests.acceptance import run_gitlabform
from gitlabform.constants import EXIT_PROCESSING_ERROR

pytestmark = pytest.mark.requires_license


class TestGroupVariablesPremium:
    """Test suite for GitLab group variable operations with Premium features.

    Tests variable creation, updates, deletion using gitlabform configuration that.
    requires GitLab Premium license.
    """

    def test__add_new_variables_with_env_scope(self, group):
        """Test case: add new variables with environment scope."""

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
              FOO_scoped_variable:
                key: FOO
                value: prod-value
                environment_scope: prod
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-value"
        assert variables[1].environment_scope == "prod"

    def test__update_variables_with_env_scope(self, group):
        """Test case: update variables that were added in previous test case"""

        # Verify that 3 initial variables have been set because 'group' is class scoped fixture and the last test case result will set 3 variables.
        assert len(group.variables.list(get_all=True)) == 2

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              # Not configuring 'FOO' variable with default scope. Expect that to remain as-is
              FOO_scoped_variable:
                key: FOO
                value: prod-new-value
                environment_scope: prod
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        # Expect 'FOO' variable with default scope to remain unchanged because it was not in the config
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-new-value"
        assert variables[1].environment_scope == "prod"

    def test__delete_variables_with_env_scope(self, group, capsys):
        """Test case: Variable deletion scenarios"""

        # Clear any existing variables from previous tests since 'group' is class-scoped
        existing = group.variables.list(get_all=True)
        for var in existing:
            group.variables.delete(var.key, filter={"environment_scope": var.environment_scope})

        # Set initial variables for all test scenarios
        initial_vars = [
            {"key": "KEY_SCOPE", "value": "any", "environment_scope": "prod"},  # for key-scope match delete
            {"key": "WRONG_SCOPE", "value": "value", "environment_scope": "prod"},  # for wrong scope test
            {   # for attribute match tests
                "key": "MULTI_ATTR",
                "value": "test-xyz-123",
                "protected": True,
                "masked": True,
                "variable_type": "env_var",
                "environment_scope": "prod"
            }
        ]
        for var in initial_vars:
            group.variables.create(var)

        # Verify initial state
        assert len(group.variables.list(get_all=True)) == 3

        # Test 1: Delete with key and scope match
        config_key_scope = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              key_scope_var:
                key: KEY_SCOPE
                environment_scope: prod
                delete: true
        """
        run_gitlabform(config_key_scope, group)
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2  # Only WRONG_SCOPE and MULTI_ATTR should remain
        assert not any(v.key == "KEY_SCOPE" for v in variables)

        # Test 2: Delete should fail with wrong scope
        config_wrong_scope = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              wrong_scope_var:
                key: WRONG_SCOPE
                environment_scope: dev  # wrong scope, actual is 'prod'
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_wrong_scope, group)
        captured = capsys.readouterr()
        assert "Cannot delete variable 'WRONG_SCOPE' with scope 'dev' - variable does not exist" in captured.err

        # Test 3: Delete should fail when specified attributes don't match
        config_mismatch = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              multi_attr_var:
                key: MULTI_ATTR
                value: test-xyz-123     # match
                protected: False        # doesn't match
                environment_scope: prod # match
                delete: true
        """
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config_mismatch, group)
        captured = capsys.readouterr()
        assert "Cannot delete MULTI_ATTR - attributes don't match" in captured.err

        # Test 4: Delete should succeed when providing subset of attributes
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
                environment_scope: prod # match
                delete: true
        """
        run_gitlabform(config_partial, group)
        variables = group.variables.list(get_all=True)
        assert len(variables) == 1  # Only WRONG_SCOPE should remain
        assert not any(v.key == "MULTI_ATTR" for v in variables)


    def test__raw_parameter_passing(self, group):
        """Test case: validate raw parameter passing design works by setting extra optional attributes for variables"""

        # The previous test case using 'group' fixture ends with 1 variables.
        variables = group.variables.list(get_all=True)
        assert len(variables) == 1

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_variables:
              FOO_scoped_variable:
                description: this is a prod scoped protected and masked variable
                key: FOO
                value: foo-123-xyz  # value must follow masking requirement
                protected: true
                masked: true
                environment_scope: prod
                filter[environment_scope]: prod
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
        assert variables[1].environment_scope == "prod"


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
              FOO_scoped_variable:
                key: FOO
                value: foo-123-xyz-new-value  # value must follow masking requirement as previously it was configured
                environment_scope: prod
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 2

        # Expect 'FOO' variable with default scope to remain unchanged because it was not in the config
        assert variables[0].key == "WRONG_SCOPE"
        assert variables[0].value == "value"
        assert variables[0].environment_scope == "prod"
        # Expect 'FOO' variable with prod scope to be updated
        # and other attributes to remain as-is
        # because they were not specified in the config
        # and were set in the previous test case
        assert variables[1].description == "this is a prod scoped protected and masked variable"
        assert variables[1].key == "FOO"
        assert variables[1].value == "foo-123-xyz-new-value"
        assert variables[1].protected is True
        assert variables[1].masked is True
        assert variables[1].environment_scope == "prod"

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
            {"key": "FOO", "value": "123", "environment_scope": "dev"},  # should not change because gitlabform config will be same
            {"key": "FOO", "value": "prod-value", "environment_scope": "prod"},  # should be deleted because of ommission in gitlabform config and 'enforce' mode
            {"key": "BAR", "value": "456", "environment_scope": "dev"},  # should be updated because gitlabform config will apply new value
            {"key": "BAZ", "value": "789", "environment_scope": "dev"},  # should be deleted because gitlabform config will use the 'delete' key
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
                environment_scope: dev
              FOO_variable:
                key: FOO
                value: 123
                environment_scope: dev
              BAR_variable:
                key: BAR
                value: 456_updated
                environment_scope: dev
              BAZ_variable:
                key: BAZ
                environment_scope: dev
                delete: true
        """
        run_gitlabform(config, group)

        # Verify results
        variables = group.variables.list(get_all=True)
        assert len(variables) == 3
        assert variables[0].key == "FOO"
        assert variables[0].value == "123"
        assert variables[0].environment_scope == "dev"
        assert variables[1].key == "BAR"
        assert variables[1].value == "456_updated"
        assert variables[1].environment_scope == "dev"
        assert variables[2].key == "NEW"
        assert variables[2].value == "new-var-value"
        assert variables[2].environment_scope == "dev"
