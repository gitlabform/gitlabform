import pytest

from gitlabform.gitlab.core import UnexpectedResponseException

from tests.acceptance import run_gitlabform


class TestSecretVariables:
    def test__builds_disabled(self, gitlab, group_and_project):
        config_builds_not_enabled = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: disabled
            secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_builds_not_enabled, group_and_project)

        with pytest.raises(UnexpectedResponseException):
            # secret variables will NOT be available without builds_access_level in ['private', 'enabled']
            gitlab.get_secret_variables(group_and_project)

    def test__single_secret_variable(self, gitlab, group_and_project):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        assert len(secret_variables) == 1

    def test__delete_secret_variable(self, gitlab, group_and_project):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123"

        config_delete_secret_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123
                delete: true
        """

        run_gitlabform(config_delete_secret_variable, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        assert len(secret_variables) == 0

    def test__reset_single_secret_variable(self, gitlab, group_and_project):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123"

        config_single_secret_variable2 = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123456
        """

        run_gitlabform(config_single_secret_variable2, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123456"

    def test__more_secret_variables(self, gitlab, group_and_project):
        config_more_secret_variables = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            secret_variables:
              foo:
                key: FOO
                value: 123456
              bar:
                key: BAR
                value: bleble
        """

        run_gitlabform(config_more_secret_variables, group_and_project)

        secret_variables = gitlab.get_secret_variables(group_and_project)
        secret_variables_keys = set([secret["key"] for secret in secret_variables])
        assert len(secret_variables) == 2
        assert secret_variables_keys == {"FOO", "BAR"}
