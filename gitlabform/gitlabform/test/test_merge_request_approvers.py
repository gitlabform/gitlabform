import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, create_users_in_project, \
    add_users_to_group, get_gitlab, GROUP_NAME

PROJECT_NAME = 'merge_requests_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME

USER_BASE_NAME = 'merge_requests_user'  # user1, user2, ...

GROUP_WITH_USER1_AND_USER2 = 'gitlabform_tests_group_with_user1_and_user2'

GROUP_WITH_USER3 = 'gitlabform_tests_group_with_user3'

GROUP_WITH_USER4 = 'gitlabform_tests_group_with_user4'

DEVELOPER_ACCESS = 30


@pytest.fixture(scope="function")
def gitlab(request):

    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    create_users_in_project(USER_BASE_NAME, 4, GROUP_AND_PROJECT_NAME)

    create_group(GROUP_WITH_USER1_AND_USER2)
    add_users_to_group(GROUP_WITH_USER1_AND_USER2, ['merge_requests_user1', 'merge_requests_user2'])

    create_group(GROUP_WITH_USER3)
    add_users_to_group(GROUP_WITH_USER3, ['merge_requests_user3'])

    create_group(GROUP_WITH_USER4)
    add_users_to_group(GROUP_WITH_USER4, ['merge_requests_user4'])

    gl = get_gitlab()

    def fin():
        # remove all the approval rules and disable approvals in the project
        rules = gl.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        for rule in rules:
            gl.delete_approvals_rule(GROUP_AND_PROJECT_NAME, rule['id'])
        gl.put_project_settings(GROUP_AND_PROJECT_NAME, {'merge_requests_access_level': 'disabled'})

    request.addfinalizer(fin)
    return gl  # provide fixture value


config__approvers_single_user = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user1
"""

config__approvers_single_user_change = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user2
"""

config__approvers_single_group = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approver_groups:
        - gitlabform_tests_group_with_user1_and_user2
"""

config__approvers_single_group_change = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approver_groups:
        - gitlabform_tests_group_with_user4
"""

config__approvers_single_user_and_single_group = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user1
      approver_groups:
        - gitlabform_tests_group_with_user4
"""

config__approvers_single_user_and_single_group_change = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user2
      approver_groups:
        - gitlabform_tests_group_with_user1_and_user2
"""

config__approvers_more_than_one_user = """
gitlab:
  api_version: 4

project_settings:
  gitlabform_tests_group/merge_requests_project:
    project_settings:
      merge_requests_access_level: "enabled"
    merge_requests:
      approvals:
        approvals_before_merge: 1
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - merge_requests_user1
        - merge_requests_user2
"""


class TestMergeRequestApprovers:

    def test__if_it_works__single_user(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_user, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user1'
        assert len(rules[0]['groups']) == 0

    def test__if_change_works__only_users(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_user, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user1'
        assert len(rules[0]['groups']) == 0

        gf = GitLabForm(config_string=config__approvers_single_user_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user2'
        assert len(rules[0]['groups']) == 0

    def test__if_it_works__single_group(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_group, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user1_and_user2'
        assert len(rules[0]['users']) == 0

    def test__if_change_works__single_group_change(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_group, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user1_and_user2'
        assert len(rules[0]['users']) == 0

        gf = GitLabForm(config_string=config__approvers_single_group_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user4'
        assert len(rules[0]['users']) == 0

    def test__if_it_works__single_user_and_single_group(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_user_and_single_group, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user1'
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user4'

    def test__if_change_works__single_user_and_single_group_change(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_single_user_and_single_group, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user1'
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user4'

        gf = GitLabForm(config_string=config__approvers_single_user_and_single_group_change, project_or_group=GROUP_AND_PROJECT_NAME)
        gf.main()

        rules = gitlab.get_approvals_rules(GROUP_AND_PROJECT_NAME)
        assert len(rules) == 1
        assert len(rules[0]['users']) == 1
        assert rules[0]['users'][0]['username'] == 'merge_requests_user2'
        assert len(rules[0]['groups']) == 1
        assert rules[0]['groups'][0]['name'] == 'gitlabform_tests_group_with_user1_and_user2'

    def test__if_fails_with_system_exit__more_than_one_user(self, gitlab):
        gf = GitLabForm(config_string=config__approvers_more_than_one_user, project_or_group=GROUP_AND_PROJECT_NAME)
        with pytest.raises(SystemExit):
            gf.main()
