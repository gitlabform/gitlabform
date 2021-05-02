import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    get_gitlab,
    GROUP_NAME,
)

PROJECT_NAME = "project_settings_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    gl = get_gitlab()

    def fin():
        gl.delete_project(GROUP_AND_PROJECT_NAME)

    request.addfinalizer(fin)
    return gl  # provide fixture value


config_builds_for_private_projects = f"""
project_settings:
  {GROUP_AND_PROJECT_NAME}:
    project_settings:
      builds_access_level: private
      visibility: private
"""


class TestProjectSettings:
    def test__builds_for_private_projects(self, gitlab):
        gf = GitLabForm(
            config_string=config_builds_for_private_projects,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        settings = gitlab.get_project_settings(GROUP_AND_PROJECT_NAME)
        assert settings["visibility"] == "private"
        # there is no such field in the "Get single project" API :/
        # assert settings['builds_access_level'] is 'private'
