import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, get_gitlab, create_readme_in_project, \
    GROUP_NAME

PROJECT_NAME = 'branches_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)
    create_readme_in_project(GROUP_AND_PROJECT_NAME)  # in master branch
    gl.create_branch(GROUP_AND_PROJECT_NAME, 'branch1', 'master')
    gl.create_branch(GROUP_AND_PROJECT_NAME, 'branch2', 'master')
    gl.create_branch(GROUP_AND_PROJECT_NAME, 'branch3', 'master')
    gl.create_branch(GROUP_AND_PROJECT_NAME, 'branch4', 'master')

    def fin():
        # the only thing needed to clean up after below tests is deleting all created branches
        gl.delete_branch(GROUP_AND_PROJECT_NAME, 'branch1')
        gl.delete_branch(GROUP_AND_PROJECT_NAME, 'branch2')
        gl.delete_branch(GROUP_AND_PROJECT_NAME, 'branch3')
        gl.delete_branch(GROUP_AND_PROJECT_NAME, 'branch4')

    request.addfinalizer(fin)
    return gl  # provide fixture value


protect_branch_but_allow_pushes = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      branch1:
        protected: true
        developers_can_push: true
        developers_can_merge: true
"""

protect_branch_and_disallow_pushes = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      branch2:
        protected: true
        developers_can_push: false
        developers_can_merge: false
"""

mixed_config = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      branch3:
        protected: true
        developers_can_push: false
        developers_can_merge: true
      branch4:
        protected: false
"""


class TestBranches:

    def test__protect_branch_but_allow_pushes(self, gitlab):
        gf = GitLabForm(config_string=protect_branch_but_allow_pushes,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'branch1')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is True
        assert branch['developers_can_merge'] is True

    def test__protect_branch_and_disallow_pushes(self, gitlab):
        gf = GitLabForm(config_string=protect_branch_and_disallow_pushes,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'branch2')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is False
        assert branch['developers_can_merge'] is False

    def test__mixed_config(self, gitlab):
        gf = GitLabForm(config_string=mixed_config,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'branch3')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is False
        assert branch['developers_can_merge'] is True

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'branch4')
        assert branch['protected'] is False
