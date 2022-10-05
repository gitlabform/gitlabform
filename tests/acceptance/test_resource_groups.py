import pytest
from tests.acceptance import run_gitlabform
import time


@pytest.fixture(scope="function")
def add_gitlab_ci_config(group_and_project):
    add_gitlab_ci_config = f"""
    projects_and_groups:
      {group_and_project}:
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
    run_gitlabform(add_gitlab_ci_config, group_and_project)
    return group_and_project


class TestResourceGroups:
    def test__update_resource_group_process_mode(
        self, gitlab, group_and_project, add_gitlab_ci_config
    ):
        update_resource_group_config = f"""
        projects_and_groups:
          {group_and_project}:
            resource_groups:
              production:
                process_mode: newest_first
            """

        time.sleep(5)
        run_gitlabform(update_resource_group_config, group_and_project)

        resource_group = gitlab.get_specific_resource_group(
            group_and_project, "production"
        )
        assert resource_group["key"] == "production"
        assert resource_group["process_mode"] == "newest_first"
