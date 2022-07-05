import pytest

from gitlabform.gitlab.core import UnexpectedResponseException

from tests.acceptance import run_gitlabform


class TestVariables:
    def test__builds_disabled(self, gitlab, group_and_project):
        config_builds_not_enabled = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: disabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_builds_not_enabled, group_and_project)

        with pytest.raises(UnexpectedResponseException):
            # variables will NOT be available without builds_access_level in ['private', 'enabled']
            gitlab.get_variables(group_and_project)

    def test__single_variable(self, gitlab, group_and_project):
        config_single_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        assert len(variables) == 1

    def test__delete_variable(self, gitlab, group_and_project):
        config_single_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        assert len(variables) == 1
        assert variables[0]["value"] == "123"

        config_delete_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
                delete: true
        """

        run_gitlabform(config_delete_variable, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        assert len(variables) == 0

    def test__reset_single_variable(self, gitlab, group_and_project):
        config_single_variable = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        assert len(variables) == 1
        assert variables[0]["value"] == "123"

        config_single_variable2 = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123456
        """

        run_gitlabform(config_single_variable2, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        assert len(variables) == 1
        assert variables[0]["value"] == "123456"

    def test__more_variables(self, gitlab, group_and_project):
        config_more_variables = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123456
              bar:
                key: BAR
                value: bleble
        """

        run_gitlabform(config_more_variables, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        variables_keys = set([variable["key"] for variable in variables])
        assert len(variables) == 2
        assert variables_keys == {"FOO", "BAR"}
