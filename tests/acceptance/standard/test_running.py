import pytest
from tests.acceptance import (
    run_gitlabform,
)


class TestRunning:
    # noinspection PyPep8Naming
    def test__ALL(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          '*':
            project_settings:
              request_access_enabled: true
        """

        run_gitlabform(config, "ALL")

        project = gl.projects.get(project.id)
        assert project.request_access_enabled is True

        other_project = gl.projects.get(other_project.id)
        assert other_project.request_access_enabled is True

    # noinspection PyPep8Naming
    def test__ALL_DEFINED(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        run_gitlabform(config, "ALL_DEFINED")

        project = gl.projects.get(project.id)
        assert project.suggestion_commit_message == "foobar"

        project = gl.projects.get(other_project.id)
        assert project.suggestion_commit_message != "foobar"

        config = f"""
        projects_and_groups:
          non/existent_project:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, "ALL_DEFINED")

        config = f"""
        projects_and_groups:
          non_existent_group/*:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, "ALL_DEFINED")

        config = f"""
        projects_and_groups:
          group_to_create/*:
            create_if_not_found: true
            group_settings:
              suggestion_commit_message: 'foobar'
        """

        run_gitlabform(config, "ALL_DEFINED")
        created_group = gl.groups.get("group_to_create")
        assert created_group.suggestion_commit_message == "foobar"

        config = f"""
        projects_and_groups:
          group_to_create/project_to_create:
            create_if_not_found: true
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        run_gitlabform(config, "ALL_DEFINED")
        created_project = gl.projects.get(
            "group_to_create/project_to_create"
        )
        assert created_project.suggestion_commit_message == "foobar"
