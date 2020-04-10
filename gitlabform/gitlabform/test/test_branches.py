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

    branches = ['protect_branch_but_allow_all', 'protect_branch_and_disallow_all',
                'protect_branch_and_allow_merges', 'protect_branch_and_allow_pushes']
    for branch in branches:
        gl.create_branch(GROUP_AND_PROJECT_NAME, branch, 'master')

    def fin():
        # delete all created branches
        for branch_to_delete in branches:
            gl.delete_branch(GROUP_AND_PROJECT_NAME, branch_to_delete)

    request.addfinalizer(fin)
    return gl  # provide fixture value


protect_branch_but_allow_all = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      protect_branch_but_allow_all:
        protected: true
        developers_can_push: true
        developers_can_merge: true
"""

protect_branch_and_disallow_all = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      protect_branch_and_disallow_all:
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
      protect_branch_and_allow_merges:
        protected: true
        developers_can_push: false
        developers_can_merge: true
      protect_branch_and_allow_pushes:
        protected: true
        developers_can_push: true
        developers_can_merge: false
"""

unprotect_branches = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      protect_branch_and_allow_merges:
        protected: false
      protect_branch_and_allow_pushes:
        protected: false
"""

mixed_config_with_new_api = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/branches_project:
    branches:
      protect_branch_and_allow_merges:
        push_access_level: 0
        merge_access_level: 30
        unprotect_access_level: 40
      protect_branch_and_allow_pushes:
        push_access_level: 30
        merge_access_level: 30
        unprotect_access_level: 40
"""


class TestBranches:

    def test__protect_branch_but_allow_all(self, gitlab):
        gf = GitLabForm(config_string=protect_branch_but_allow_all,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_but_allow_all')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is True
        assert branch['developers_can_merge'] is True

    def test__protect_branch_and_disallow_all(self, gitlab):
        gf = GitLabForm(config_string=protect_branch_and_disallow_all,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_disallow_all')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is False
        assert branch['developers_can_merge'] is False

    def test__mixed_config(self, gitlab):
        gf = GitLabForm(config_string=mixed_config,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_merges')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is False
        assert branch['developers_can_merge'] is True

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_pushes')
        assert branch['protected'] is True
        assert branch['developers_can_push'] is True
        assert branch['developers_can_merge'] is False

        gf = GitLabForm(config_string=unprotect_branches,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_merges')
        assert branch['protected'] is False

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_pushes')
        assert branch['protected'] is False

    def test__mixed_config_with_new_api(self, gitlab):
        gf = GitLabForm(config_string=mixed_config_with_new_api,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_merges')
        assert branch['push_access_level'] is 0
        assert branch['merge_access_level'] is 30
        assert branch['unprotect_access_level'] is 40

        branch = gitlab.get_branch(GROUP_AND_PROJECT_NAME, 'protect_branch_and_allow_pushes')
        assert branch['push_access_level'] is 30
        assert branch['merge_access_level'] is 30
        assert branch['unprotect_access_level'] is 40