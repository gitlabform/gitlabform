import pytest

from gitlabform.test import (
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_owner(gitlab, group, groups, sub_group, users):

    gitlab.add_member_to_group(group, users[0], 50)
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

    gitlab.remove_share_from_group(group, sub_group)
    for share_with in groups:
        gitlab.remove_share_from_group(group, share_with)


class TestGroupSharedWith:
    def test__add_group(self, gitlab, group, users, groups, one_owner):
        no_of_members_before = len(gitlab.get_group_members(group))

        add_shared_with = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 50
            group_shared_with:
              {groups[0]}:
                group_access_level: 30
              {groups[1]}:
                group_access_level: 30
        """

        run_gitlabform(add_shared_with, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before, members

        shared_with = gitlab.get_group_shared_with(group)
        assert len(shared_with) == 2

    def test__sub_group(self, gitlab, group, users, sub_group, one_owner):
        no_of_members_before = len(gitlab.get_group_members(group))

        add_shared_with = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 50
            group_shared_with:
              {sub_group}:
                group_access_level: 30
        """

        run_gitlabform(add_shared_with, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before, members

        shared_with = gitlab.get_group_shared_with(group)
        assert len(shared_with) == 1

    def test__remove_group(self, gitlab, group, users, groups, one_owner):

        gitlab.add_share_to_group(group, groups[0], 50)
        gitlab.add_share_to_group(group, groups[1], 50)

        no_of_members_before = len(gitlab.get_group_members(group))
        no_of_shared_with_before = len(gitlab.get_group_shared_with(group))

        remove_group = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {users[0]}:
                access_level: 50
            group_shared_with:
              {groups[0]}:
                group_access_level: 30
        """

        run_gitlabform(remove_group, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before

        shared_with = gitlab.get_group_shared_with(group)
        assert len(shared_with) == no_of_shared_with_before - 1

        assert [sw["group_name"] for sw in shared_with] == [groups[0]]

    def test__not_remove_groups_with_enforce_false(
        self, gitlab, group, users, groups, one_owner
    ):

        no_of_members_before = len(gitlab.get_group_members(group))
        no_of_shared_with_before = len(gitlab.get_group_shared_with(group))

        setups = [
            # flag explicitly set to false
            f"""
            projects_and_groups:
              {group}/*:
                enforce_group_members: false
                group_members:
                  {users[0]}:
                    access_level: 50
                group_shared_with: []
            """,
            # flag not set at all (but the default is false)
            f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  {users[0]}:
                    access_level: 50
                group_shared_with: []
            """,
        ]
        for setup in setups:
            run_gitlabform(setup, group)

            members = gitlab.get_group_members(group)
            assert len(members) == no_of_members_before

            members_usernames = {member["username"] for member in members}
            assert members_usernames == {
                f"{users[0]}",
            }

            shared_with = gitlab.get_group_shared_with(group)
            assert len(shared_with) == no_of_shared_with_before

    def test__change_group_access(self, gitlab, group, groups, users, one_owner):

        change_some_users_access = f"""
        projects_and_groups:
          {group}/*:
            group_members:
              {users[0]}:
                access_level: 50
            group_shared_with:
              {groups[0]}:
                group_access_level: 30
              {groups[1]}:
                group_access_level: 50
        """

        run_gitlabform(change_some_users_access, group)

        shared_with = gitlab.get_group_shared_with(group)
        for shared_with_group in shared_with:
            if shared_with_group["group_name"] == f"{groups[0]}":
                assert shared_with_group["group_access_level"] == 30
            if shared_with_group["group_name"] == f"{groups[1]}":
                assert shared_with_group["group_access_level"] == 50

    def test__remove_all(self, gitlab, group, users, one_owner):
        no_shared_with = f"""
        projects_and_groups:
          {group}/*:
            enforce_group_members: true
            group_members:
              {users[0]}:
                access_level: 50
            group_shared_with: []
        """

        run_gitlabform(no_shared_with, group)

        shared_with = gitlab.get_group_shared_with(group)
        assert len(shared_with) == 0
