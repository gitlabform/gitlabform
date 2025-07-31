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

    def test__add_new_variables(self, project):
        """Test case: add new variables"""

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
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 3

        assert variables[0].key == "FOO"
        assert variables[0].value == "foo123"
        assert variables[0].environment_scope == "*"  # default scope if not configured

        assert variables[1].key == "FOO"
        assert variables[1].value == "prod-value"
        assert variables[1].environment_scope == "prod"

        assert variables[2].key == "BAR"
        assert variables[2].value == "bar-value"
        assert variables[2].environment_scope == "*"  # default scope if not configured

    def test__update_variables(self, project):
        """Test case: update variables that were added in previous test case"""

        # Verify that 3 initial variables have been set because 'project' is class scoped fixture and the last test case result will set 3 variables.
        assert len(project.variables.list(get_all=True)) == 3

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
        assert len(variables) == 3

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

    def test__delete_variables(self, project, capsys):
        """Test case: delete variables that were added/updated in previous test cases"""

        # Verify that 3 initial variables have been set because 'project' is class scoped fixture and the last test case result will set 3 variables.
        assert len(project.variables.list(get_all=True)) == 3

        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              # Delete following variable even though 'value' is not provided
              FOO_default_scoped_variable:
                key: FOO
                delete: true
              # Delete following variable where both key and value is provided
              BAR_variable:
                key: BAR
                value: bar-value-updated
                delete: true
              # Delete following variable that specifies key and environment_scope
              FOO_scoped_variable:
                key: FOO
                environment_scope: prod
                delete: true
        """
        run_gitlabform(config, project)

        # Verify results
        variables = project.variables.list(get_all=True)
        assert len(variables) == 0

        # Now test deleting a variable by providing a config that contains correct key but wrong value.
        # It should not delete that variable because the search shouldn't match.

        # First set inital variables for test
        initial_vars = [
            {"key": "FOO", "value": "foo-123"},
            {"key": "BAR", "value": "bar-123", "environment_scope": "prod"},
        ]
        for var in initial_vars:
            project.variables.create(var)

        # Verify that 2 initial variables have been set
        assert len(project.variables.list(get_all=True)) == 2

        # Apply gitlabform config containig wrong value for FOO that has deafult scope '*'
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              FOO_default_scoped_variable:
                key: FOO
                value: this is a wrong value
                delete: true
        """

        # TODO: This test should run like this
        # with pytest.raises(SystemExit) as exec_info:
        #     run_gitlabform(config, project)

        run_gitlabform(config, project)

        variables = project.variables.list(get_all=True)
        assert len(variables) == 1

        assert variables[0].key == "BAR"
        assert variables[0].value == "bar-123"
        assert variables[0].environment_scope == "prod"

        # Now test deleting a variable with environment scope (i.e. BAR) but it's not specified
        error_message_for_delete_without_scope = (
            "To delete a variable with scope, make sure to specify 'environment_scope' in the config"
        )
        # Apply gitlabform config
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              BAR_prod_scoped_variable:
                key: BAR
                delete: true
        """
        # Verify results
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, project)

        captured_output = capsys.readouterr()

        assert exc_info.value.code == 2
        assert exc_info.type == SystemExit
        assert exc_info.value.code == EXIT_PROCESSING_ERROR
        assert error_message_for_delete_without_scope in captured_output.err

        # Now test deleting variable with envrionment scope but wrong value for the variable
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            variables:
              BAR_prod_scoped_variable:
                key: BAR
                value: this is a wrong value
                environment_scope: prod
                delete: true
        """

        # TODO: This test should run like this
        # with pytest.raises(SystemExit) as exec_info:
        #     run_gitlabform(config, project)

        run_gitlabform(config, project)

        variables = project.variables.list(get_all=True)
        assert len(variables) == 0

    def test__raw_parameter_passing(self, project):
        """Test case: validate raw parameter passing design works by setting extra optional attributes for variables"""

        # The previous test case using 'project' fixture ends with 0 variables.
        variables = project.variables.list(get_all=True)
        assert len(variables) == 0

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
        assert len(variables) == 1

        assert variables[0].description == "this is a prod scoped protected and masked variable"
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo-123-xyz"
        assert variables[0].protected is True
        assert variables[0].masked is True
        assert variables[0].environment_scope == "prod"

    def test__preserve_unconfigured_attributes(self, project):
        """Test case: When updating a variable, any attributes that is not in config, should remain as-is"""

        # The previous test case using 'project' fixture ends with 1 variables.
        variables = project.variables.list(get_all=True)
        assert len(variables) == 1

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
        assert len(variables) == 1

        assert variables[0].description == "this is a prod scoped protected and masked variable"
        assert variables[0].key == "FOO"
        assert variables[0].value == "foo-123-xyz-new-value"
        assert variables[0].protected is True
        assert variables[0].masked is True
        assert variables[0].environment_scope == "prod"

    def test__enforce_mode_delete_all_variables(self, project):
        """Test case: Enforce mode - delete all variables"""

        # Initial variables should already be set for the 'project' because it's a class scoped fixture.
        # Ensure the project has correct number of variables from the latest state of previous test.
        assert len(project.variables.list(get_all=True)) == 1

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
              Variable_value_with_complex_value:
                key: COMPLEX_VALUE
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
        assert len(variables) == 2
        assert variables[0].key == "SPECIAL_CHARS"
        assert variables[0].value == "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert variables[1].key == "COMPLEX_VALUE"
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
        assert variables[1].value == expected_message
