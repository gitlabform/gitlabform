import pytest

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, get_gitlab, create_readme_in_project, \
    GROUP_NAME

PROJECT_NAME = 'push_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME


@pytest.fixture(scope="module")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)
    gl = get_gitlab()

    def fin():
        gl.delete_project(GROUP_AND_PROJECT_NAME)

    request.addfinalizer(fin)
    return gl  # provide fixture value


set_project_push_rules = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/push_project:
    project_push_rules:
      commit_message_regex: 'Fixes \d +'
      branch_name_regex: ""
      deny_delete_tag: false
      member_check: false
      prevent_secrets: false
      author_email_regex: ""
      file_name_regex: ""
      max_file_size: 0 # in MB, 0 means unlimited
"""

setup_project_push_rules = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/push_project:
    project_push_rules:
      commit_message_regex: 'Fixes \d +'
      branch_name_regex: ""
      deny_delete_tag: false
      member_check: false
      prevent_secrets: false
      author_email_regex: ""
      file_name_regex: ""
      max_file_size: 2 # in MB, 0 means unlimited
"""


class Helpers:

    @staticmethod
    def setup_push_rules(gitlab: GitLab):
        gf = GitLabForm(config_string=setup_project_push_rules,
                        project_or_group=GROUP_NAME)
        gf.main()

        push_rules = gitlab.get_project_push_rules(GROUP_AND_PROJECT_NAME)
        assert push_rules['max_file_size'] == 2


class TestFiles:

    def test__apply_push_rules(self, gitlab: GitLab):
        Helpers.setup_push_rules(gitlab)

    def test__edit_push_rules(self, gitlab: GitLab):
        Helpers.setup_push_rules(gitlab)
        gf = GitLabForm(config_string=set_project_push_rules,
                        project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        push_rules = gitlab.get_project_push_rules(GROUP_AND_PROJECT_NAME)
        assert push_rules['max_file_size'] == 0
