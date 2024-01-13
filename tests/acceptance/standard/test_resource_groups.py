import pytest
from tests.acceptance import run_gitlabform
import time


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
        time.sleep(5)

        resource_group = project.resource_groups.get("production")
        assert resource_group.key == "production"
        assert resource_group.process_mode == "newest_first"

    def test__ensure_exists_false(self, project, add_gitlab_ci_config):
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
        except Exception as exc:
            assert False, f"'run_gitlabform' raised an exception {exc}"
