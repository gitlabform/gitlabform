import pytest

import pdb 
import logging

import json

logger = logging.getLogger(__name__)

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


config_tag_permission_no_access = (
    """
gitlab:
  api_version: 4

project_settings:
  """
    + GROUP_AND_PROJECT_NAME
    + """:
    project_settings:
        default_branch: main
        tags:
            "*":
                protected: true
                create_access_level: 0 
            "v*":
                protected: true
                create_access_level: 40

"""
)


class TestTagPermissionNoAccess:
    def test__tag_permission_no_access(self, gitlab):
        gf = GitLabForm(
            config_string=config_tag_permission_no_access,
            project_or_group=GROUP_AND_PROJECT_NAME,
        )
        gf.main()

        project = gitlab.get_project(GROUP_AND_PROJECT_NAME)

        assert project["archived"] is False

