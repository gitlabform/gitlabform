import pytest

from gitlabform.gitlabform.test import (
    create_users,
    delete_users,
    run_gitlabform,
)


@pytest.fixture(scope="class")
def users(request, group):
    create_users(f"{group}_user", 4)

    def fin():
        # we need to ensure none of the created users is the sole Owner
        # of the group, as then we would not be able to delete it
        base_users_setup = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              root: # creator of the group
                access_level: 50
        """
        run_gitlabform(base_users_setup, group)
        delete_users(f"{group}_user", 4)

    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(request, gitlab, users, group):
    one_owner_and_two_developers = f"""
    projects_and_groups:
      {group}/*:
        enforce_group_members: true
        group_members:
          {group}_user1:
            access_level: 50
          {group}_user2:
            access_level: 30
          {group}_user3:
            access_level: 30
    """
    run_gitlabform(one_owner_and_two_developers, group)

    def fin():
        original_users_setup = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              root: # creator of the group
                access_level: 50
        """
        run_gitlabform(original_users_setup, group)

    request.addfinalizer(fin)


class TestGroupMembers:
    def test__add_users(self, gitlab, group, one_owner_and_two_developers):

        no_of_members_before = len(gitlab.get_group_members(group))
        user_to_add1 = f"{group}_user3"
        user_to_add2 = f"{group}_user4"

        add_users = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              root: # creator of the group
                access_level: 50
              {group}_user1:
                access_level: 30
              {group}_user2:
                access_level: 30
              {user_to_add1}: # new user 1
                access_level: 30
              {user_to_add2}: # new user 2
                access_level: 30
        """

        run_gitlabform(add_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before + 2

        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(user_to_add1) == 1
        assert members_usernames.count(user_to_add2) == 1

    def test__remove_users(self, gitlab, group, one_owner_and_two_developers):

        no_of_members_before = len(gitlab.get_group_members(group))
        user_to_remove = f"{group}_user3"

        remove_users = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {group}_user1:
                access_level: 50
              {group}_user2:
                access_level: 30
        """

        run_gitlabform(remove_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before - 1

        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(user_to_remove) == 0

    def test__not_remove_users_with_enforce_false(
        self, gitlab, group, one_owner_and_two_developers
    ):

        no_of_members_before = len(gitlab.get_group_members(group))

        setups = [
            # flag explicitly set to false
            f"""
            projects_and_groups:
              {group}/*:
                enforce_group_members: false
                group_members:
                  {group}_user1:
                    access_level: 50
                  {group}_user2:
                    access_level: 30
            """,
            # flag not set at all (but the default is false)
            f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  {group}_user1:
                    access_level: 50
                  {group}_user2:
                    access_level: 30
            """,
        ]
        for setup in setups:
            run_gitlabform(setup, group)

            members = gitlab.get_group_members(group)
            assert len(members) == no_of_members_before

            members_usernames = {member["username"] for member in members}
            assert members_usernames == {
                f"{group}_user1",
                f"{group}_user2",
                f"{group}_user3",
            }

    def test__change_some_users_access(
        self, gitlab, group, one_owner_and_two_developers
    ):

        new_access_level = 40

        change_some_users_access = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {group}_user1:
                access_level: 50
              {group}_user2:
                access_level: {new_access_level} # changed level
              {group}_user3:
                access_level: {new_access_level} # changed level
        """

        run_gitlabform(change_some_users_access, group)

        members = gitlab.get_group_members(group)
        for member in members:
            if member["username"] == f"{group}_user1":
                assert member["access_level"] == 50
            if member["username"] == f"{group}_user2":
                assert member["access_level"] == new_access_level
            if member["username"] == f"{group}_user3":
                assert member["access_level"] == new_access_level

    def test__change_owner(self, gitlab, group, one_owner_and_two_developers):

        change_owner = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {group}_user1:
                access_level: 30 # only developer now
              {group}_user2:
                access_level: 50 # new owner
              {group}_user3:
                access_level: 30
        """

        run_gitlabform(change_owner, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 3

        for member in members:
            if member["username"] == f"{group}_user1":
                assert member["access_level"] == 30  # only developer now
            if member["username"] == f"{group}_user2":
                assert member["access_level"] == 50  # new owner
            if member["username"] == f"{group}_user3":
                assert member["access_level"] == 30

    def test__zero_owners(self, gitlab, group, users):
        zero_owners = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {group}_user4:
                access_level: 40
        """

        with pytest.raises(SystemExit):
            run_gitlabform(zero_owners, group)

    def test__zero_users(self, gitlab, group, users):

        zero_users = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members: {{}}
        """

        with pytest.raises(SystemExit):
            run_gitlabform(zero_users, group)
