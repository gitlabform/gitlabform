import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, create_users_in_project, \
    add_users_to_group, get_gitlab, GROUP_NAME

PROJECT_NAME = 'merge_requests_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME

USER_BASE_NAME = 'merge_requests_user'  # user1, user2, ...

GROUP_WITH_USER1_AND_USER2 = 'gitlabform_tests_group_with_user1_and_user2'

GROUP_WITH_USER4 = 'gitlabform_tests_group_with_user4'

DEVELOPER_ACCESS = 30


@pytest.fixture(scope="module")
def gitlab(request):

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    create_users_in_project(USER_BASE_NAME, 4, GROUP_AND_PROJECT_NAME)

    create_group(GROUP_WITH_USER1_AND_USER2)
    add_users_to_group(GROUP_WITH_USER1_AND_USER2, ['merge_requests_user1', 'merge_requests_user2'])

    create_group(GROUP_WITH_USER4)
    add_users_to_group(GROUP_WITH_USER4, ['merge_requests_user4'])

    gl = get_gitlab()

    def fin():
        # the only thing needed to clean up after below tests is disabling merge requests for the project
        # completely - this should reset project's MR approvers and approver groups lists
        gl.put_project_settings(GROUP_AND_PROJECT_NAME, {'merge_requests_access_level': 'disabled'})

    request.addfinalizer(fin)
    return gl  # provide fixture value


config__approvers_only_users = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user1
        - merge_requests_user2
"""

config__approvers_only_users_change = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user1
"""

config__approvers_only_groups = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approver_groups:
        - gitlabform_tests_group_with_user1_and_user2
"""

config__approvers_only_groups_change = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approver_groups:
        - gitlabform_tests_group_with_user1_and_user2
        - gitlabform_tests_group_with_user4
"""

config__approvers_both = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user3
      approver_groups:
        - gitlabform_tests_group_with_user4
"""

config__approvers_both_groups_change = """
gitlab:
  api_version: 4

project_settings:
  group1/project1:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user3
      approver_groups:
        - gitlabform_tests_group_with_user4
        - gitlabform_tests_group_with_user1_and_user2
"""

config__approvers_both_users_change = """
gitlab:
  api_version: 4

project_settings:
  group1/project1:
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user2
        - merge_requests_user3
      approver_groups:
        - gitlabform_tests_group_with_user4
"""


class TestMergeRequestApprovers:

    def test__if_it_works__only_users(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_only_users, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        assert len(approvers['approvers']) == 2

    def test__if_change_works__only_users(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_only_users, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        # approvers = 2

        gf = GitLabForm(config_string=config__approvers_only_users_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        assert len(approvers['approvers']) == 1

    def test__if_it_works__only_groups(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_only_groups, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        assert len(approvers['approver_groups']) == 1

    def test__if_change_works__only_groups(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_only_groups, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        # approvers_groups = 1

        gf = GitLabForm(config_string=config__approvers_only_groups_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        assert len(approvers['approver_groups']) == 2

    def test__if_it_works__both(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_both, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        assert len(approvers['approvers']) == 1
        assert len(approvers['approver_groups']) == 1

    def test__if_change_works__both__groups_change(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_both, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        # approvers = 1, approvers_groups = 1

        gf = GitLabForm(config_string=config__approvers_both_groups_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        print(str(approvers))
        assert len(approvers['approvers']) == 1
        assert len(approvers['approver_groups']) == 2

    def test__if_change_works__both__users_change(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_both, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        # approvers = 1, approvers_groups = 1

        gf = GitLabForm(config_string=config__approvers_both_users_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        approvers = gitlab.get_approvers(GROUP_AND_PROJECT_NAME)
        print(str(approvers))
        assert len(approvers['approvers']) == 2
        assert len(approvers['approver_groups']) == 1
