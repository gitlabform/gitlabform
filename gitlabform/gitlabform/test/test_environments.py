import time
import operator
import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
    GROUP_NAME,
)

PROJECT_NAME = "environments_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="function")
def gitlab(request):
    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    gl = get_gitlab()

    def fin():
        gl.delete_project(GROUP_AND_PROJECT_NAME)
        time.sleep(5)

    request.addfinalizer(fin)
    return gl  # provide fixture value


config_delete_environment = (
    """
gitlab:
  api_version: 4

project_settings:
  """
    + GROUP_AND_PROJECT_NAME
    + """:
        environments:
            PROD:
                name: PROD
                delete: true
"""
)

config_stop_environment = (
    """
gitlab:
  api_version: 4

project_settings:
  """
    + GROUP_AND_PROJECT_NAME
    + """:
        environments:
            PROD:
                name: PROD
                stop: true
"""
)

config_update_environment = (
    """
gitlab:
  api_version: 4

project_settings:
  """
    + GROUP_AND_PROJECT_NAME
    + """:
        environments:
            PROD:
                name: PROD
                external_url: https://localhost/prod
                new_name: Production
            TST:
                name: TEST
                new_external_url: https://localhost/test
"""
)

config_create_environment = (
    """
gitlab:
  api_version: 4

group_settings:
  """
    + GROUP_NAME
    + """:
        environments:
            PROD:
                name: PROD
                external_url: https://localhost
                delete: false

project_settings:
  """
    + GROUP_AND_PROJECT_NAME
    + """:
        environments:
            TST:
                name: TEST
                external_url: https://localhost
"""
)


class TestEnvironments:
    def test__get_all_environments(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project_environments = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(project_environments) == 2
        assert "TEST" in map(operator.itemgetter("name"), project_environments)
        assert "PROD" in map(operator.itemgetter("name"), project_environments)

    def test__get_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()
        environment = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "PROD")
        assert environment["name"] == "PROD"
        assert environment["state"] == "available"
        assert environment["external_url"] == "https://localhost"

    def test__stop_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        environment = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(environment) == 2

        gf = GitLabForm(
            config_string=config_stop_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        environment = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "PROD")
        assert environment["name"] == "PROD"
        assert environment["state"] == "stopped"

    def test__delete_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project_environments = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(project_environments) == 2

        gf = GitLabForm(
            config_string=config_delete_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()
        project_environments = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(project_environments) == 1
        assert "TEST" in map(operator.itemgetter("name"), project_environments)

    def test__put_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project_environments = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(project_environments) == 2
        assert "TEST" in map(operator.itemgetter("name"), project_environments)
        assert "PROD" in map(operator.itemgetter("name"), project_environments)

        gf = GitLabForm(
            config_string=config_update_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project_environments = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(project_environments) == 2
        assert "TEST" in map(operator.itemgetter("name"), project_environments)
        assert "Production" in map(operator.itemgetter("name"), project_environments)

        environment = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "Production")
        assert environment["state"] == "available"
        assert environment["external_url"] == "https://localhost/prod"

        environment = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "TEST")
        assert environment["state"] == "available"
        assert environment["external_url"] == "https://localhost/test"
