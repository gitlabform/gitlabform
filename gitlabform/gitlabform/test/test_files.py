import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, get_gitlab, create_readme_in_project, \
    GROUP_NAME

PROJECT_NAME = 'files_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)
    create_readme_in_project(GROUP_AND_PROJECT_NAME)  # in master branch
    for branch in ['protected_branch1', 'protected_branch2', 'regular_branch1', 'regular_branch2']:
        gl.create_branch(GROUP_AND_PROJECT_NAME, branch, 'master')

    def fin():
        # delete all created branches
        for branch_to_delete in ['protected_branch1', 'protected_branch2', 'regular_branch1', 'regular_branch2']:
            gl.delete_branch(GROUP_AND_PROJECT_NAME, branch_to_delete)

    request.addfinalizer(fin)
    return gl  # provide fixture value


set_file_specific_branch = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/files_project:
    files:
      "README.md":
        overwrite: true
        branches:
          - master
        content: "Content for master only"
"""

set_file_all_branches = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/files_project:
    files:
      "README.md":
        overwrite: true
        branches: all
        content: "Content for all branches"
"""

set_file_protected_branches = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/files_project:
    branches:
      protected_branch1:
        protected: true
      protected_branch2:
        protected: true
    files:
      "README.md":
        overwrite: true
        branches: protected
        content: "Content for protected branches only"
"""


class TestFiles:

    def test__set_file_specific_branch(self, gitlab):
        gf = GitLabForm(config_string=set_file_specific_branch,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        file_content = gitlab.get_file(GROUP_AND_PROJECT_NAME, 'master', 'README.md')
        assert file_content == 'Content for master only'

        other_branch_file_content = gitlab.get_file(GROUP_AND_PROJECT_NAME, 'protected_branch1', 'README.md')
        assert other_branch_file_content == 'Hello World!'

    def test__set_file_all_branches(self, gitlab):
        gf = GitLabForm(config_string=set_file_all_branches,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        for branch in ['master', 'protected_branch1', 'protected_branch2', 'regular_branch1', 'regular_branch2']:
            file_content = gitlab.get_file(GROUP_AND_PROJECT_NAME, branch, 'README.md')
            assert file_content == 'Content for all branches'

    def test__set_file_protected_branches(self, gitlab):
        gf = GitLabForm(config_string=set_file_protected_branches,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        for branch in ['protected_branch1', 'protected_branch2']:
            file_content = gitlab.get_file(GROUP_AND_PROJECT_NAME, branch, 'README.md')
            assert file_content == 'Content for protected branches only'

        for branch in ['master', 'regular_branch1', 'regular_branch2']:
            file_content = gitlab.get_file(GROUP_AND_PROJECT_NAME, branch, 'README.md')
            assert not file_content == 'Content for protected branches only'
