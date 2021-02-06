import time

import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    create_group,
    create_project_in_group,
    create_readme_in_project,
    get_gitlab,
    GROUP_NAME,
)

PROJECT_NAME = "archive_project"
GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME


@pytest.fixture(scope="function")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)
    create_readme_in_project(GROUP_AND_PROJECT_NAME)  # in main branch

    def fin():
        gl.delete_project(GROUP_AND_PROJECT_NAME)
        # TODO: find some smarter way to avoid 400 when trying to create project while it is still being deleted
        time.sleep(15)

    request.addfinalizer(fin)
    return gl  # provide fixture value


archive_project = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/archive_project:
    project:
      archive: true
"""

unarchive_project = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/archive_project:
    project:
      archive: false
"""

edit_archived_project = """
gitlab:
  api_version: 4

# the project has to be configured as archived
# for other configs for it to be ignored
project_settings:
  gitlabform_tests_group/archive_project:
    project:
      archive: true

group_settings:
  gitlabform_tests_group:
    files:
      README.md:
        overwrite: true
        branches:
          - main
        content: |
          Some other content that the default one
"""


class TestArchiveProject:
    def test__archive_project(self, gitlab):
        gf = GitLabForm(
            config_string=archive_project,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project = gitlab.get_project(GROUP_AND_PROJECT_NAME)

        assert project["archived"] is True

    def test__unarchive_project(self, gitlab):
        gf = GitLabForm(
            config_string=archive_project,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project = gitlab.get_project(GROUP_AND_PROJECT_NAME)

        assert project["archived"] is True

        gf = GitLabForm(
            config_string=unarchive_project,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project = gitlab.get_project(GROUP_AND_PROJECT_NAME)

        assert project["archived"] is False

    def test__dont_edit_archived_project(self, gitlab):
        gf = GitLabForm(
            config_string=archive_project,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project = gitlab.get_project(GROUP_AND_PROJECT_NAME)

        assert project["archived"] is True

        gf = GitLabForm(
            config_string=edit_archived_project,
            project_or_group=GROUP_NAME,
        )
        gf.main()

        # if we tried to edit an archived project, then we will get an exception here
