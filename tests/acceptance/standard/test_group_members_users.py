import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    allowed_codes,
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(group, root_user, users):

    group.members.create(
        {"user_id": users[0].id, "access_level": AccessLevel.OWNER.value}
    )
    group.members.create(
        {"user_id": users[1].id, "access_level": AccessLevel.DEVELOPER.value}
    )
    group.members.create(
        {"user_id": users[2].id, "access_level": AccessLevel.DEVELOPER.value}
    )
    group.members.delete(root_user.id)

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    group.members.create(
        {"user_id": root_user.id, "access_level": AccessLevel.OWNER.value}
    )

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        with allowed_codes(404):
            group.members.delete(user.id)


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

    def test__not_remove_users_with_enforce_false(
        self, group, users, one_owner_and_two_developers
    ):

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

    def test__change_some_users_access(
        self, group, users, one_owner_and_two_developers
    ):
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

    def test__change_owner(self, group, users, one_owner_and_two_developers):

        change_owner = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.DEVELOPER.value} # only developer now
                    {users[1].username}:
                      access_level: {AccessLevel.OWNER.value} # new owner
                    {users[2].username}:
                      access_level: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(change_owner, group)

        members = group.members.list()
        assert len(members) == 3

        for member in members:
            if member.username == f"{users[0].username}":
                assert (
                    member.access_level == AccessLevel.DEVELOPER.value
                )  # only developer now
            if member.username == f"{users[1].username}":
                assert member.access_level == AccessLevel.OWNER.value  # new owner
            if member.username == f"{users[2].username}":
                assert member.access_level == AccessLevel.DEVELOPER.value

    def test__add_user_with_access_level_name(
        self, group, users, one_owner_and_two_developers
    ):

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

    def test__root_as_the_sole_owner(self, gitlab, group):
        config = f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  users:
                    root:
                      access_level: {AccessLevel.OWNER.value}
                  enforce: true
            """

        run_gitlabform(config, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 1

        assert members[0]["username"] == "root"
        assert members[0]["access_level"] == AccessLevel.OWNER.value
