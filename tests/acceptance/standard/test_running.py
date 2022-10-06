import pytest
from tests.acceptance import (
    run_gitlabform,
)


class TestRunning:
    # noinspection PyPep8Naming
    def test__ALL(self, gitlab, group, project, other_project):
        config = f"""
        projects_and_groups:
          '*':
            project_settings:
              request_access_enabled: true
        """

        run_gitlabform(config, "ALL")

        project = gitlab.get_project(f"{group}/{project}")
        assert project["request_access_enabled"] is True

        other_project = gitlab.get_project(f"{group}/{other_project}")
        assert other_project["request_access_enabled"] is True

    # noinspection PyPep8Naming
    def test__ALL_DEFINED(self, gitlab, group, project, other_project):
        group_and_project = f"{group}/{project}"

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        run_gitlabform(config, "ALL_DEFINED")

        project = gitlab.get_project(group_and_project)
        assert project["suggestion_commit_message"] == "foobar"

        group_and_other_project = f"{group}/{other_project}"
        project = gitlab.get_project(group_and_other_project)
        assert project["suggestion_commit_message"] != "foobar"

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
