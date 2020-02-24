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


some_users = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user1:
        access_level: 50
      group_member_user2:
        access_level: 30
      group_member_user3:
        access_level: 40
"""

add_users = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user1:
        access_level: 50
      group_member_user2:
        access_level: 30
      group_member_user3:
        access_level: 40
      group_member_user4: # new user
        access_level: 40
"""

remove_users = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user1:
        access_level: 50
      group_member_user3:
        access_level: 40
"""

change_some_users_access = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user1:
        access_level: 50
      group_member_user2:
        access_level: 40 # changed level
      group_member_user3:
        access_level: 30 # changed level
"""

one_owner = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user4:
        access_level: 50
"""

change_owner = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user3: # new Owner
        access_level: 50
"""

zero_owners = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members:
      group_member_user4:
        access_level: 40
"""

zero_users = """
gitlab:
  api_version: 4

group_settings:
  gitlabform_tests_group:
    group_members: {}
"""


class TestGroupMembers:

    def __setup_some_users(self, gitlab):
        gf = GitLabForm(config_string=some_users,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 3
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user2') == 1
        assert members_usernames.count('group_member_user3') == 1

    def test__setup_users(self, gitlab):
        self.__setup_some_users(gitlab)

    def test__add_users(self, gitlab):
        self.__setup_some_users(gitlab)

        gf = GitLabForm(config_string=add_users,
                        project_or_group=GROUP_NAME)
        gf.main()
        
        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 4
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user2') == 1
        assert members_usernames.count('group_member_user3') == 1
        assert members_usernames.count('group_member_user4') == 1

    def test__remove_users(self, gitlab):
        self.__setup_some_users(gitlab)

        gf = GitLabForm(config_string=remove_users,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 2
        members_usernames = [member['username'] for member in members]
        assert members_usernames.count('group_member_user1') == 1
        assert members_usernames.count('group_member_user3') == 1

    def test__change_some_users_access(self, gitlab):
        self.__setup_some_users(gitlab)

        gf = GitLabForm(config_string=change_some_users_access,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 3
        for member in members:
            if member['username'] == 'group_member_user1':
                assert member['access_level'] == 50
            if member['username'] == 'group_member_user2':
                assert member['access_level'] == 40
            if member['username'] == 'group_member_user3':
                assert member['access_level'] == 30

    def test__change_owner(self, gitlab):
        gf = GitLabForm(config_string=one_owner,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 1
        assert members[0]['access_level'] == 50
        assert members[0]['username'] == 'group_member_user4'

        gf = GitLabForm(config_string=change_owner,
                        project_or_group=GROUP_NAME)
        gf.main()

        members = gitlab.get_group_members(GROUP_NAME)
        assert len(members) == 1
        assert members[0]['access_level'] == 50
        assert members[0]['username'] == 'group_member_user3'

    def test__zero_owners(self, gitlab):
        gf = GitLabForm(config_string=zero_owners,
                        project_or_group=GROUP_NAME)
        with pytest.raises(SystemExit):
            gf.main()

    def test__zero_users(self, gitlab):
        gf = GitLabForm(config_string=zero_owners,
                        project_or_group=GROUP_NAME)
        with pytest.raises(SystemExit):
            gf.main()
