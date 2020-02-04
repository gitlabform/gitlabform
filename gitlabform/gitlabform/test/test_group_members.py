import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_users, remove_users_from_group, get_gitlab, GROUP_NAME


USER_BASE_NAME = 'group_member_user'  # user1, user2, ...


@pytest.fixture(scope="function")
def gitlab(request):
    gl = get_gitlab()

    create_group(GROUP_NAME)
    create_users(USER_BASE_NAME, 4)

    def fin():
        remove_users_from_group(GROUP_NAME, ['group_member_user1', 'group_member_user2', 'group_member_user3',
                                             'group_member_user4'])

    request.addfinalizer(fin)
    return gl  # provide fixture value


add_user1_and_user2 = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user1:
        access_level: 40
      group_member_user2:
        access_level: 30
"""

add_user3 = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user3:
        access_level: 40
"""

add_user4 = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user4:
        access_level: 40
"""

change_user4 = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user4:
        access_level: 30
"""


class TestGroupMembers:

    def test__add_user1_and_user2(self, gitlab):
        gf = GitLabForm(config_string=add_user1_and_user2,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        # root user that created the group is one of the members as owner
        assert len(members) == 3
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user2') == 1

    def test__add_user1_and_user2_and_then_add_user3(self, gitlab):
        gf = GitLabForm(config_string=add_user1_and_user2,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        # root user that created the group is one of the members as owner
        assert len(members) == 3
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user2') == 1
        
        gf = GitLabForm(config_string=add_user3,
                        project_or_group=GROUP_NAME)
        gf.main()
        
        members = gitlab.get_group_members(GROUP_NAME)
        # we DO NOT remove existing users with gitlabform (yet)!
        assert len(members) == 3 + 1
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user2') == 1
        assert members_usernames.count('group_member_user3') == 1

    def test__add_and_then_change_user4_access_level(self, gitlab):
        gf = GitLabForm(config_string=add_user4,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        # root user that created the group is one of the members as owner
        assert len(members) == 2
        for member in members:
            if member['username'] == 'group_member_user4':
                assert member['access_level'] == 40

        gf = GitLabForm(config_string=change_user4,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        # root user that created the group is one of the members as owner
        assert len(members) == 2
        for member in members:
            if member['username'] == 'group_member_user4':
                assert member['access_level'] == 30
