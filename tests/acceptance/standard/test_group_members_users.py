import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    allowed_codes,
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(group, root_user, users):
    yield from one_owner_and_two_developers_for_group_non_fixture(group, root_user, users)


@pytest.fixture(scope="function")
def one_owner_and_two_developers_group_for_function(group_for_function, root_user, users_for_function):
    yield from one_owner_and_two_developers_for_group_non_fixture(group_for_function, root_user, users_for_function)


def one_owner_and_two_developers_for_group_non_fixture(group_to_add_members_to, root_user_account, users_to_add):
    group_to_add_members_to.members.create({"user_id": users_to_add[0].id, "access_level": AccessLevel.OWNER.value})
    group_to_add_members_to.members.create({"user_id": users_to_add[1].id, "access_level": AccessLevel.DEVELOPER.value})
    group_to_add_members_to.members.create({"user_id": users_to_add[2].id, "access_level": AccessLevel.DEVELOPER.value})

    group_to_add_members_to.members.delete(root_user_account.id)

    yield group_to_add_members_to

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.
    group_to_add_members_to.members.create({"user_id": root_user_account.id, "access_level": AccessLevel.OWNER.value})

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users_to_add:
        with allowed_codes(404):
            group_to_add_members_to.members.delete(user.id)


@pytest.fixture(scope="function")
def one_bot_member(gl, make_group_access_token):
    token = make_group_access_token()
    bot_user = gl.users.get(token.user_id)

    yield bot_user.username

    token.delete()


class TestGroupMembersUsers:
    def test__add_user(self, group, users, one_owner_and_two_developers):
        no_of_members_before = len(group.members.list())
        user_to_add = f"{users[3].username}"

        add_users = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
                    {users[1].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {users[2].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {user_to_add}: # new user 1
                      access_level: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(add_users, group)

        members = group.members.list()
        assert len(members) == no_of_members_before + 1

        members_usernames = [member.username for member in members]
        assert members_usernames.count(user_to_add) == 1

    def test__remove_user(self, group, users, one_owner_and_two_developers):
        no_of_members_before = len(group.members.list())
        user_to_remove = f"{users[2].username}"

        remove_users = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
                    {users[1].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
                  enforce: true
            """

        run_gitlabform(remove_users, group)

        members = group.members.list()
        assert len(members) == no_of_members_before - 1

        members_usernames = [member.username for member in members]
        assert user_to_remove not in members_usernames

    def test__remove_user_keep_bots(self, group, users, one_owner_and_two_developers, one_bot_member):
        no_of_members_before = len(group.members.list())
        user_to_remove = f"{users[2].username}"

        remove_users = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
                    {users[1].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
                  enforce: true
                  keep_bots: true
            """

        run_gitlabform(remove_users, group)

        members = group.members.list()
        assert len(members) == no_of_members_before - 1

        members_usernames = [member.username for member in members]
        assert user_to_remove not in members_usernames

        assert one_bot_member in members_usernames

    def test__not_remove_users_with_enforce_false(self, group, users, one_owner_and_two_developers):
        no_of_members_before = len(group.members.list())

        setups = [
            # flag explicitly set to false
            f"""
                projects_and_groups:
                  {group.full_path}/*:
                    group_members:
                      users:
                        {users[0].username}:
                          access_level: {AccessLevel.OWNER.value}
                        {users[1].username}:
                          access_level: {AccessLevel.DEVELOPER.value}
                      enforce: false
                """,
            # flag not set at all (but the default is false)
            f"""
                projects_and_groups:
                  {group.full_path}/*:
                    group_members:
                      users:
                        {users[0].username}:
                          access_level: {AccessLevel.OWNER.value}
                        {users[1].username}:
                          access_level: {AccessLevel.DEVELOPER.value}
                """,
        ]
        for setup in setups:
            run_gitlabform(setup, group)

            members = group.members.list()
            assert len(members) == no_of_members_before

            members_usernames = {member.username for member in members}
            assert members_usernames == {
                f"{users[0].username}",
                f"{users[1].username}",
                f"{users[2].username}",
            }

    def test__change_some_users_access(self, group, users, one_owner_and_two_developers):
        new_access_level = AccessLevel.MAINTAINER.value

        change_some_users_access = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
                    {users[1].username}:
                      access_level: {new_access_level} # changed level
                    {users[2].username}:
                      access_level: {new_access_level} # changed level
            """

        run_gitlabform(change_some_users_access, group)

        members = group.members.list()
        for member in members:
            if member.username == f"{users[0].username}":
                assert member.access_level == AccessLevel.OWNER.value
            if member.username == f"{users[1].username}":
                assert member.access_level == new_access_level
            if member.username == f"{users[2].username}":
                assert member.access_level == new_access_level

    def test__change_owner(
        self, group_for_function, users_for_function, one_owner_and_two_developers_group_for_function
    ):
        members = group_for_function.members.list()

        assert len(members) == 3

        for member in members:
            if member.username == f"{users_for_function[0].username}":
                assert member.access_level == AccessLevel.OWNER.value
            if member.username == f"{users_for_function[1].username}":
                assert member.access_level == AccessLevel.DEVELOPER.value
            if member.username == f"{users_for_function[2].username}":
                assert member.access_level == AccessLevel.DEVELOPER.value

        change_owner = f"""
            projects_and_groups:
              {group_for_function.full_path}/*:
                group_members:
                  users:
                    {users_for_function[0].username}:
                      access_level: {AccessLevel.DEVELOPER.value} # only developer now
                    {users_for_function[1].username}:
                      access_level: {AccessLevel.OWNER.value} # new owner
                    {users_for_function[2].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(change_owner, group_for_function)

        members = group_for_function.members.list()
        assert len(members) == 3

        for member in members:
            if member.username == f"{users_for_function[0].username}":
                assert member.access_level == AccessLevel.DEVELOPER.value  # only developer now
            if member.username == f"{users_for_function[1].username}":
                assert member.access_level == AccessLevel.OWNER.value  # new owner
            if member.username == f"{users_for_function[2].username}":
                assert member.access_level == AccessLevel.DEVELOPER.value

    def test__add_user_with_access_level_name(self, group, users, one_owner_and_two_developers):
        no_of_members_before = len(group.members.list())
        user_to_add = f"{users[3].username}"

        add_users = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              {users[0].username}:
                access_level: owner
              {users[1].username}:
                access_level: developer
              {users[2].username}:
                access_level: developer
              {user_to_add}: # new user 1
                access_level: developer
        """

        run_gitlabform(add_users, group)

        members = group.members.list()
        assert len(members) == no_of_members_before + 1

        members_usernames = [member.username for member in members]
        assert members_usernames.count(user_to_add) == 1

    def test__root_as_the_sole_owner(self, group):
        config = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    root:
                      access_level: {AccessLevel.OWNER.value}
                  enforce: true
            """

        run_gitlabform(config, group)

        members = group.members.list()
        assert len(members) == 1

        assert members[0].username == "root"
        assert members[0].access_level == AccessLevel.OWNER.value
