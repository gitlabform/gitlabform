import pytest

from tests.acceptance import run_gitlabform
from gitlabform.constants import EXIT_PROCESSING_ERROR

pytestmark = pytest.mark.requires_license


class TestGroupVariablesPremium:
    """Test suite for GitLab group variable operations with Premium features.

    Tests variable creation, updates, deletion using gitlabform configuration that.
    requires GitLab Premium license.
    """

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
