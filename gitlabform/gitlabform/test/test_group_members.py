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
def some_users_setup(request, gitlab, users, group):
    some_users_setup = f"""
    projects_and_groups:
      {group}/*:
        enforce_group_members: true
        group_members:
          root: # creator of the group
            access_level: 50
          {group}_user2:
            access_level: 30
          {group}_user3:
            access_level: 40
    """
    run_gitlabform(some_users_setup, group)

    def fin():
        base_users_setup = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              root: # creator of the group
                access_level: 50
        """
        run_gitlabform(base_users_setup, group)

    request.addfinalizer(fin)


class TestGroupMembers:
    def test__add_users(self, gitlab, group, some_users_setup):
        add_users = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              root: # creator of the group
                access_level: 50
              {group}_user1:
                access_level: 50
              {group}_user2:
                access_level: 30
              {group}_user3:
                access_level: 40
              {group}_user4: # new user
                access_level: 40
        """

        run_gitlabform(add_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 5
        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(f"{group}_user4") == 1

    def test__remove_users(self, gitlab, group, some_users_setup):
        remove_users = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {group}_user1:
                access_level: 50
              {group}_user4:
                access_level: 40
        """

        run_gitlabform(remove_users, group)
        members = gitlab.get_group_members(group)
        assert len(members) == 2
        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(f"{group}_user1") == 1
        assert members_usernames.count(f"{group}_user4") == 1

        assert members_usernames.count("root") == 0
        assert members_usernames.count(f"{group}_user2") == 0
        assert members_usernames.count(f"{group}_user3") == 0

    def test__not_remove_users_with_enforce_false(
        self, gitlab, group, some_users_setup
    ):
        not_remove_users_with_enforce_false = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: false
            group_members:
              root: # creator of the group
                access_level: 50
              {group}_user2:
                access_level: 30
        """

        run_gitlabform(not_remove_users_with_enforce_false, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 3
        members_usernames = [member["username"] for member in members]
        print(members_usernames)
        assert members_usernames.count("root") == 1
        assert members_usernames.count(f"{group}_user2") == 1
        assert members_usernames.count(f"{group}_user3") == 1

    def test__not_remove_users_without_enforce(self, gitlab, group, some_users_setup):
        not_remove_users_without_enforce = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              root: # creator of the group
                access_level: 50
              {group}_user2:
                access_level: 30
        """

        run_gitlabform(not_remove_users_without_enforce, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 3
        members_usernames = [member["username"] for member in members]
        print(members_usernames)
        assert members_usernames.count("root") == 1
        assert members_usernames.count(f"{group}_user2") == 1
        assert members_usernames.count(f"{group}_user3") == 1

    def test__change_some_users_access(self, gitlab, group, some_users_setup):

        change_some_users_access = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              root: # creator of the group
                access_level: 50
              {group}_user2:
                access_level: 40 # changed level
              {group}_user3:
                access_level: 30 # changed level
        """

        run_gitlabform(change_some_users_access, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 3
        for member in members:
            if member["username"] == "root":
                assert member["access_level"] == 50
            if member["username"] == f"{group}_user2":
                assert member["access_level"] == 40
            if member["username"] == f"{group}_user3":
                assert member["access_level"] == 30

    def test__change_owner(self, gitlab, group, users):
        one_owner = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              root: # creator of the group
                access_level: 50
        """

        run_gitlabform(one_owner, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 1
        assert members[0]["access_level"] == 50
        assert members[0]["username"] == "root"

        change_owner = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {group}_user3: # new Owner
                access_level: 50
        """

        run_gitlabform(change_owner, group)

        members = gitlab.get_group_members(group)
        assert len(members) == 1
        assert members[0]["access_level"] == 50
        assert members[0]["username"] == f"{group}_user3"

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
