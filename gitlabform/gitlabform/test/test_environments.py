import operator
import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
    GROUP_NAME,
)

PROJECT_NAME = "project_environments_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="function")
def gitlab(request):
    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    gl = get_gitlab()
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

        e = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(e) == 2
        assert "TEST" in map(operator.itemgetter("name"), e)
        assert "PROD" in map(operator.itemgetter("name"), e)

    def test__get_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()
        e = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "PROD")
        assert e["name"] == "PROD"
        assert e["state"] == "available"
        assert e["external_url"] == "https://localhost"

    def test__stop_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        e = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(e) == 2

        gf = GitLabForm(
            config_string=config_stop_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        e = gitlab.get_environment(GROUP_AND_PROJECT_NAME, "PROD")
        assert e["name"] == "PROD"
        assert e["state"] == "stopped"

    def test__delete_environment(self, gitlab):
        gf = GitLabForm(
            config_string=config_create_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        e = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(e) == 2

        gf = GitLabForm(
            config_string=config_delete_environment,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()
        e = gitlab.get_all_environments(GROUP_AND_PROJECT_NAME)
        assert len(e) == 1
        assert "TEST" in map(operator.itemgetter("name"), e)
