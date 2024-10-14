import pytest
import time

from tests.acceptance import run_gitlabform
from gitlabform.constants import EXIT_PROCESSING_ERROR


@pytest.fixture(scope="function")
def add_gitlab_ci_config(project):
    add_gitlab_ci_config = f"""
    projects_and_groups:
      {project.path_with_namespace}:
        files:
          ".gitlab-ci.yml":
            branches: 
              - main
            overwrite: true
            content: |
              stages:
                - deploy

              deploy:
                stage: deploy
                script:
                  - echo deploy
                environment: production
                resource_group: production
        """
    run_gitlabform(add_gitlab_ci_config, project)
    time.sleep(5)

    return project


class TestResourceGroups:
    def test__update_resource_group_process_mode(self, project, add_gitlab_ci_config):
        update_resource_group_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            resource_groups:
              production:
                process_mode: newest_first
            """

        run_gitlabform(update_resource_group_config, project)

        resource_group = project.resource_groups.get("production")
        assert resource_group.key == "production"
        assert resource_group.process_mode == "newest_first"

    def test__resource_group_process_mode_invalid_value(
        self, project, add_gitlab_ci_config, capsys
    ):
        update_resource_group_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            resource_groups:
              production:
                process_mode: foo
            """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(update_resource_group_config, project)

        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert "Resource group update failed" in captured.err

    def test__ensure_exists_default_true(self, project, capsys):
        update_resource_group_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            resource_groups:
              resource_group_that_dont_exist:
                process_mode: newest_first
            """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(update_resource_group_config, project)
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert "Project is not configured to use resource group" in captured.err

    def test__ensure_exists_equals_true(self, project, capsys):
        update_resource_group_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            resource_groups:
              ensure_exists: true
              resource_group_that_dont_exist:
                process_mode: newest_first
            """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(update_resource_group_config, project)
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert "Project is not configured to use resource group" in captured.err

    def test__ensure_exists_equals_false(self, project):
        update_resource_group_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            resource_groups:
              ensure_exists: false
              resource_group_that_dont_exist:
                process_mode: newest_first
            """

        try:
            run_gitlabform(update_resource_group_config, project)
        except Exception as exception:
            assert (
                False
            ), f"Test disabling `ensure_exists` raised an exception {exception}, but it shouldn't."
