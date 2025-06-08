from logging import warning, fatal
from typing import Any, Dict, List, Union
from io import StringIO

import pytest
from ruamel.yaml import YAML
from gitlab.exceptions import GitlabGetError, GitlabListError, GitlabDeleteError

from tests.acceptance import run_gitlabform


class TestGroupVariables:
    """Test suite for GitLab group variable operations.

    Tests variable creation, updates, deletion, and environment-scoped variables
    using gitlabform configuration.
    """

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        """Set up test method."""
        self.yaml = YAML()
        self.yaml.indent(mapping=2, sequence=4, offset=2)

        # Access the 'group' fixture
        self.group = request.getfixturevalue("group")

        # Cleanup: Delete all variables in the group
        # This is to ensure that the group is clean before each test
        try:
            variables = self.group.variables.list(get_all=True)
        except GitlabListError:
            warning(f"Failed to list variables for group {self.group.full_path}")

        for var in variables:
            print(f"Deleting variable {var}")
            try:
                self.group.variables.delete(var.key, filter={"environment_scope": var.environment_scope})
            except GitlabDeleteError as error:
                fatal(f"Unexpected error occurred while deleting existing variables: {error}")

    @pytest.mark.parametrize(
        "initial_vars, config_vars, expected",
        # fmt: off
        # Disable Black formatting for test data to:
        # 1. Keep data compact and aligned for better readability
        # 2. Preserve meaningful indentation and alignment of comments
        # 3. Prevent splitting of test cases across too many lines
        [
            # Basic operations
            # Test case 1: Single variable - no change
            ([{"key": "FOO", "value": "123"}],
             [{"key": "FOO", "value": "123"}],
             [("FOO", "123")]),

            # Test case 2: Single variable - update
            ([{"key": "FOO", "value": "123"}],
             [{"key": "FOO", "value": "123456"}],
             [("FOO", "123456")]),

            # Test case 3: Single variable - delete
            ([{"key": "FOO", "value": "123"}],
             [{"key": "FOO", "value": "123", "delete": True}],
             [("FOO", None)]),

            # Test case 4: Multiple variables - all operations
            ([{"key": "FOO", "value": "123"},      # will be updated
              {"key": "BAR", "value": "bleble"},   # will be deleted
              {"key": "BAZ", "value": "old"}],     # will stay the same
             [{"key": "FOO", "value": "123456"},   # update
              {"key": "BAR", "value": "bleble", "delete": True},  # delete
              {"key": "BAZ", "value": "old"},      # no change
              {"key": "QUX", "value": "new"}],     # create new
             [("FOO", "123456"),                   # updated
              ("BAR", None),                       # deleted
              ("BAZ", "old"),                      # unchanged
              ("QUX", "new")]),                    # newly created

            # Environment scope tests
            # Test case 5: Single variable with multiple scopes
            ([{"key": "FOO", "value": "prod-val", "environment_scope": "prod"},
              {"key": "FOO", "value": "stage-val", "environment_scope": "stage"},
              {"key": "FOO", "value": "dev-val", "environment_scope": "dev"}],
             [{"key": "FOO", "value": "new-prod", "environment_scope": "prod"},
              {"key": "FOO", "value": "stage-val", "environment_scope": "stage", "delete": True},
              {"key": "FOO", "value": "dev-val", "environment_scope": "dev"},
              {"key": "FOO", "value": "test-val", "environment_scope": "test"}],
             [("FOO", "new-prod", "prod"),
              ("FOO", None, "stage"),
              ("FOO", "dev-val", "dev"),
              ("FOO", "test-val", "test")]),

            # Test case 6: Multiple variables with multiple scopes
            ([{"key": "DB_URL", "value": "prod-db", "environment_scope": "prod"},
              {"key": "DB_URL", "value": "stage-db", "environment_scope": "stage"},
              {"key": "API_KEY", "value": "prod-key", "environment_scope": "prod"},
              {"key": "API_KEY", "value": "stage-key", "environment_scope": "stage"}],
             [{"key": "DB_URL", "value": "new-prod-db", "environment_scope": "prod"},
              {"key": "DB_URL", "value": "stage-db", "environment_scope": "stage", "delete": True},
              {"key": "DB_URL", "value": "dev-db", "environment_scope": "dev"},
              {"key": "API_KEY", "value": "prod-key", "environment_scope": "prod"},
              {"key": "API_KEY", "value": "new-stage-key", "environment_scope": "stage"},
              {"key": "API_KEY", "value": "test-key", "environment_scope": "test"}],
             [("DB_URL", "new-prod-db", "prod"),
              ("DB_URL", None, "stage"),
              ("DB_URL", "dev-db", "dev"),
              ("API_KEY", "prod-key", "prod"),
              ("API_KEY", "new-stage-key", "stage"),
              ("API_KEY", "test-key", "test")]),

            # Enforce mode tests
            # Test case 7: Enforce mode - empty configuration
            ([{"key": "FOO", "value": "123"},
              {"key": "BAR", "value": "456"}],
             {"enforce": True},                     # Only enforce flag, no variables
             []),                                   # All variables should be deleted

            # Test case 8: Enforce mode - delete unspecified variables
            ([{"key": "FOO", "value": "123"},      # will stay
              {"key": "BAR", "value": "456"},      # will be deleted
              {"key": "BAZ", "value": "789"}],     # will be deleted
             {"enforce": True,
              "foo": {"key": "FOO", "value": "123"}},  # only keep this one
             [("FOO", "123")]),                    # BAR and BAZ are deleted

            # Test case 9: Enforce mode - with updates and new variables
            ([{"key": "FOO", "value": "123"},      # will be updated
              {"key": "BAR", "value": "456"}],     # will be deleted
             {"enforce": True,
              "foo": {"key": "FOO", "value": "new123"},    # update this
              "baz": {"key": "BAZ", "value": "789"}},      # create this
             [("FOO", "new123"),                   # updated
              ("BAZ", "789")]),                    # newly created, BAR deleted

            # Test case 10: Enforce mode - with environment scopes
            ([{"key": "FOO", "value": "prod-val", "environment_scope": "prod"},
              {"key": "FOO", "value": "stage-val", "environment_scope": "stage"},
              {"key": "BAR", "value": "test-val", "environment_scope": "test"}],
             {"enforce": True,
              "foo_prod": {"key": "FOO",
                          "value": "prod-val",
                          "environment_scope": "prod"}},
             [("FOO", "prod-val", "prod")]),

            # Variable attributes tests
            # Test case 11: Raw parameters (protected, masked)
            ([],  # no initial vars
             [{"key": "PROTECTED_VAR",
               "value": "secret123",
               "protected": True,
               "masked": True}],
             [("PROTECTED_VAR", "secret123", "*", True, True)]),

            # Test case 12: Preserve protected status on update
            ([{"key": "PROTECTED_VAR",
               "value": "secret123",
               "protected": True}],
             [{"key": "PROTECTED_VAR",
               "value": "newvalue"}],
             [("PROTECTED_VAR", "newvalue", "*", True)]),

            # Test case 13: Update masked status
            ([{"key": "MASKED_VAR",
               "value": "secret123",
               "masked": True}],
             [{"key": "MASKED_VAR",
               "value": "newvalue"}],
             [("MASKED_VAR", "newvalue", "*", False, True)]),

            # Test case 14: Environment scope with enforce mode and protected/masked variables
            ([{"key": "SECRET_KEY",
               "value": "prod-secret",
               "environment_scope": "prod",
               "protected": True,
               "masked": True},
              {"key": "SECRET_KEY",
               "value": "stage-secret",
               "environment_scope": "stage",
               "protected": True,
               "masked": True}],
             {"enforce": True,
              "secret_key_prod": {"key": "SECRET_KEY",
                                 "value": "new-prod-secret",
                                 "environment_scope": "prod"}},
             [("SECRET_KEY", "new-prod-secret", "prod", True, True)]),

            # Test case 15: Special characters in value
            ([{"key": "SPECIAL_CHARS",
               "value": "!@#$%^&*()_+-=[]{}|;:,.<>?"}],
             [{"key": "SPECIAL_CHARS",
               "value": "!@#$%^&*()_+-=[]{}|;:,.<>?"}],
             [("SPECIAL_CHARS", "!@#$%^&*()_+-=[]{}|;:,.<>?")]),

            # YAML configuration tests
            # Test case 16: Complex YAML configuration handling
            ([],
             [{"key": "CONFIG_WITH_SPECIAL",
               "value": "# This represents a typical complex configuration value\n"
                       "host: ${HOST_VAR}\n"
                       "port: 8080\n"
                       "paths:\n"
                       "  - /api/v1\n"
                       "  - /api/v2"}],
             [("CONFIG_WITH_SPECIAL",
               "# This represents a typical complex configuration value\n"
               "host: ${HOST_VAR}\n"
               "port: 8080\n"
               "paths:\n"
               "  - /api/v1\n"
               "  - /api/v2")]),
        ],
        # fmt: on
        ids=[
            # Basic operations
            "test_case_1_single_var_no_change",
            "test_case_2_single_var_update",
            "test_case_3_single_var_delete",
            "test_case_4_multiple_vars_all_operations",
            # Environment scope tests
            "test_case_5_single_var_multiple_scopes",
            "test_case_6_multiple_vars_multiple_scopes",
            # Enforce mode tests
            "test_case_7_enforce_mode_empty_config",
            "test_case_8_enforce_mode_delete_unspecified",
            "test_case_9_enforce_mode_with_updates_and_new",
            "test_case_10_enforce_mode_with_environment_scopes",
            # Variable attributes tests
            "test_case_11_raw_params",
            "test_case_12_preserve_protected",
            "test_case_13_preserve_masked",
            "test_case_14_enforce_mode_with_protected_masked_scoped",
            "test_case_15_special_characters",
            # YAML configuration tests
            "test_case_16_complex_yaml_config",
        ],
    )
    def test__variables(self, initial_vars, config_vars, expected):
        """Test variable operations using gitlabform.

        Args:
            initial_vars: List of variables to create initially using GitLab API
            config_vars: List of variables to configure using gitlabform
            expected: List of (key, value) or (key, value, scope) tuples
                     representing expected variable states after configuration.
                     Value is None for variables that should be deleted.
        """
        # Set initial variables
        for var in initial_vars:
            self.group.variables.create(var)

        # Apply gitlabform config
        config = self._create_config(self.group, config_vars)
        run_gitlabform(config, self.group)

        # Verify results
        for expected_var_state in expected:
            key, value, *env_scope = expected_var_state
            get_params = {"filter": {"environment_scope": env_scope[0]}} if env_scope else {}

            if value is None:
                with pytest.raises(GitlabGetError):
                    self.group.variables.get(key, **get_params)
            else:
                variable = self.group.variables.get(key, **get_params)
                # Check value for all cases
                assert variable.value == value

                # Check additional attributes based on expected variable format:
                # (key, value)                              - Basic variable
                # (key, value, scope)                       - With environment scope
                # (key, value, scope, protected)            - With protected flag
                # (key, value, scope, protected, masked)    - With masked flag
                has_scope = len(expected_var_state) > 2
                has_protected = len(expected_var_state) > 3
                has_masked = len(expected_var_state) > 4

                if has_scope:
                    assert variable.environment_scope == expected_var_state[2]
                if has_protected:
                    assert variable.protected == expected_var_state[3]
                if has_masked:
                    assert variable.masked == expected_var_state[4]

    def _create_config(
        self,
        group,
        variables: Union[List[Dict[str, Any]], Dict[str, Any]],
    ) -> str:
        """Creates YAML configuration for GitLab project variables."""
        # Base configuration in YAML format
        base_config = f"""
projects_and_groups:
  {group.full_path}/*:
    group_variables: {{}}
"""
        config = self.yaml.load(base_config)

        # Handle enforce mode and get variable list
        if isinstance(variables, dict):
            if "enforce" in variables:
                config["projects_and_groups"][f"{group.full_path}/*"]["group_variables"]["enforce"] = True
                var_list = [variables[k] for k in variables if k != "enforce"]
            else:
                var_list = list(variables.values())  # Convert dict values to list
        else:
            var_list = variables

        # Process variables
        vars_section = {}
        for var in var_list:
            # Create unique name for variable
            name = var["key"].lower()
            if "environment_scope" in var:
                name = f"{name}_{var['environment_scope'].replace('/', '_')}"

            # Copy variable config and handle special cases
            var_config = var.copy()
            if "environment_scope" in var_config:
                var_config["filter[environment_scope]"] = var_config["environment_scope"]

            vars_section[name] = var_config

        config["projects_and_groups"][f"{group.full_path}/*"]["group_variables"].update(vars_section)

        # Convert to YAML with proper formatting
        output = StringIO()
        self.yaml.dump(config, output)
        return output.getvalue()
