import pytest

from gitlabform.test import (
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(gitlab, group, users):

    gitlab.add_member_to_group(group, users[0], 50)
    gitlab.add_member_to_group(group, users[1], 30)
    gitlab.add_member_to_group(group, users[2], 30)
    gitlab.remove_member_from_group(group, "root")

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    gitlab.add_member_to_group(group, "root", 50)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_group(group, user)


class TestGroupMembers:
    def test__add_user(self, gitlab, group, users, one_owner_and_two_developers):

        no_of_members_before = len(gitlab.get_group_members(group))
        user_to_add = f"{users[3]}"

        add_users = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 50
              {users[1]}:
                access_level: 30
              {users[2]}:
                access_level: 30
              {user_to_add}: # new user 1
                access_level: 30
        """

        run_gitlabform(add_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before + 1

        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(user_to_add) == 1

    def test__remove_user(self, gitlab, group, users, one_owner_and_two_developers):

        no_of_members_before = len(gitlab.get_group_members(group))
        user_to_remove = f"{users[2]}"

        remove_users = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {users[0]}:
                access_level: 50
              {users[1]}:
                access_level: 30
        """

        run_gitlabform(remove_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before - 1

        members_usernames = [member["username"] for member in members]
        assert user_to_remove not in members_usernames

    def test__not_remove_users_with_enforce_false(
        self, gitlab, group, users, one_owner_and_two_developers
    ):

        no_of_members_before = len(gitlab.get_group_members(group))

        setups = [
            # flag explicitly set to false
            f"""
            projects_and_groups:
              {group}/*:
                enforce_group_members: false
                group_members:
                  {users[0]}:
                    access_level: 50
                  {users[1]}:
                    access_level: 30
            """,
            # flag not set at all (but the default is false)
            f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  {users[0]}:
                    access_level: 50
                  {users[1]}:
                    access_level: 30
            """,
        ]
        for setup in setups:
            run_gitlabform(setup, group)

            members = gitlab.get_group_members(group)
            assert len(members) == no_of_members_before

            members_usernames = {member["username"] for member in members}
            assert members_usernames == {
                f"{users[0]}",
                f"{users[1]}",
                f"{users[2]}",
            }

    def test__change_some_users_access(
        self, gitlab, group, users, one_owner_and_two_developers
    ):

        new_access_level = 40

        change_some_users_access = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 50
              {users[1]}:
                access_level: {new_access_level} # changed level
              {users[2]}:
                access_level: {new_access_level} # changed level
        """

        run_gitlabform(change_some_users_access, group)

        members = gitlab.get_group_members(group)
        for member in members:
            if member["username"] == f"{users[0]}":
                assert member["access_level"] == 50
            if member["username"] == f"{users[1]}":
                assert member["access_level"] == new_access_level
            if member["username"] == f"{users[2]}":
                assert member["access_level"] == new_access_level

    def test__change_owner(self, gitlab, group, users, one_owner_and_two_developers):

        change_owner = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 30 # only developer now
              {users[1]}:
                access_level: 50 # new owner
              {users[2]}:
                access_level: 30
        """

        run_gitlabform(change_owner, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 3

        for member in members:
            if member["username"] == f"{users[0]}":
                assert member["access_level"] == 30  # only developer now
            if member["username"] == f"{users[1]}":
                assert member["access_level"] == 50  # new owner
            if member["username"] == f"{users[2]}":
                assert member["access_level"] == 30

    def test__zero_owners(self, gitlab, group, users):
        zero_owners = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {users[3]}:
                access_level: 40
        """

        with pytest.raises(SystemExit):
            run_gitlabform(zero_owners, group)

    def test__zero_users(self, gitlab, group):

        zero_users = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members: {{}}
        """

        with pytest.raises(SystemExit):
            run_gitlabform(zero_users, group)
