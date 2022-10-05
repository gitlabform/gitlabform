import pytest

from gitlabform.gitlab.core import UnexpectedResponseException, NotFoundException

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

        variable = gitlab.get_variable(group_and_project, "FOO")
        assert variable == "123"

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

        variable = gitlab.get_variable(group_and_project, "FOO")
        assert variable == "123"

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

        with pytest.raises(NotFoundException):
            gitlab.get_variable(group_and_project, "FOO")

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

        variable = gitlab.get_variable(group_and_project, "FOO")
        assert variable == "123"

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

        variable = gitlab.get_variable(group_and_project, "FOO")
        assert variable == "123456"

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

        variable = gitlab.get_variable(group_and_project, "FOO")
        assert variable == "123456"
        variable = gitlab.get_variable(group_and_project, "BAR")
        assert variable == "bleble"

    def test__variable_with_env_scope(self, gitlab, group_and_project):
        config_more_variables = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo_ee:
                key: FOO1
                value: alfa
                environment_scope: test/ee
                filter[environment_scope]: test/ee
        """

        run_gitlabform(config_more_variables, group_and_project)

        variable = gitlab.get_variable(group_and_project, "FOO1", "test/ee")
        assert variable == "alfa"

    def test__variables_with_env_scope(self, gitlab, group_and_project):
        config_more_variables = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo_ee:
                key: FOO2
                value: alfa
                environment_scope: test/ee
                filter[environment_scope]: test/ee
              foo_lv:
                key: FOO2
                value: beta
                environment_scope: test/lv
                filter[environment_scope]: test/lv
        """

        run_gitlabform(config_more_variables, group_and_project)

        variables = gitlab.get_variables(group_and_project)
        variables_keys = [variable["key"] for variable in variables]
        assert "FOO2" in variables_keys

        variable = gitlab.get_variable(group_and_project, "FOO2", "test/ee")
        assert variable == "alfa"
        variable = gitlab.get_variable(group_and_project, "FOO2", "test/lv")
        assert variable == "beta"
