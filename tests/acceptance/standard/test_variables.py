import pytest

from gitlab import GitlabGetError, GitlabListError
from gitlabform.gitlab.core import UnexpectedResponseException, NotFoundException

from tests.acceptance import run_gitlabform


class TestVariables:
    def test__builds_disabled(self, project):
        config_builds_not_enabled = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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
            project.variables.list()

    def test__single_variable(self, project):
        config_single_variable = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, project)

        variable = project.variables.get("FOO")
        assert variable.value == "123"

    def test__delete_variable(self, project):
        config_single_variable = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, project)

        variable = project.variables.get("FOO")
        assert variable.value == "123"

        config_delete_variable = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
                delete: true
        """

        run_gitlabform(config_delete_variable, project)

        with pytest.raises(GitlabGetError):
            project.variables.get("FOO")

    def test__reset_single_variable(self, project):
        config_single_variable = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, project)

        variable = project.variables.get("FOO")
        assert variable.value == "123"

        config_single_variable2 = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo:
                key: FOO
                value: 123456
        """

        run_gitlabform(config_single_variable2, project)

        variable = project.variables.get("FOO")
        assert variable.value == "123456"

    def test__more_variables(self, project):
        config_more_variables = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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

        run_gitlabform(config_more_variables, project)

        variable = project.variables.get("FOO")
        assert variable.value == "123456"
        variable = project.variables.get("BAR")
        assert variable.value == "bleble"

    def test__variable_with_env_scope(self, project):
        config_more_variables = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              builds_access_level: enabled
            variables:
              foo_ee:
                key: FOO1
                value: alfa
                environment_scope: test/ee
                filter[environment_scope]: test/ee
        """

        run_gitlabform(config_more_variables, project)

        variable = project.variables.get(
            "FOO1", filter={"environment_scope": "test/ee"}
        )
        assert variable.value == "alfa"

    def test__variables_with_env_scope(self, project):
        config_more_variables = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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

        run_gitlabform(config_more_variables, project)

        variables = project.variables.list()
        variables_keys = [variable.key for variable in variables]
        assert "FOO2" in variables_keys

        variable = project.variables.get(
            "FOO2", filter={"environment_scope": "test/ee"}
        )
        assert variable.value == "alfa"
        variable = project.variables.get(
            "FOO2", filter={"environment_scope": "test/lv"}
        )
        assert variable.value == "beta"
