import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    allowed_codes,
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_owner(root_user, group, groups, subgroup, users):
    group.members.create(
        {"user_id": users[0].id, "access_level": AccessLevel.OWNER.value}
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

    with allowed_codes(404):
        group.unshare(subgroup.id)

    for share_with in groups:
        with allowed_codes(404):
            group.unshare(share_with.id)


class TestGroupMembersGroups:
    def test__add_group(self, gl, group, users, groups, one_owner):
        no_of_members_before = len(group.members.list())

        add_shared_with = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              users:
                {users[0].username}:
                  access_level: {AccessLevel.OWNER.value}
              groups:
                {groups[0].full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
                {groups[1].full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(add_shared_with, group.full_path)

        members = group.members.list()
        assert len(members) == no_of_members_before, members

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 2

    def test__subgroup(self, gl, group, users, subgroup, one_owner):
        no_of_members_before = len(group.members.list())

        add_shared_with = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              users:
                {users[0].username}:
                  access_level: {AccessLevel.OWNER.value}
              groups:
                {subgroup.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(add_shared_with, group.full_path)

        members = group.members.list()
        assert len(members) == no_of_members_before, members

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 1

        # test second run (issue #236)
        run_gitlabform(add_shared_with, group.full_path)

    def test__remove_group(self, gl, group, users, groups, one_owner):
        group.share(groups[0].id, AccessLevel.OWNER.value)
        group.share(groups[1].id, AccessLevel.OWNER.value)

        no_of_members_before = len(group.members.list())
        no_of_shared_with_before = len(group.shared_with_groups)

        remove_group = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              enforce: true
              users:
                {users[0].username}:
                  access_level: {AccessLevel.OWNER.value}
              groups:
                {groups[0].full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(remove_group, group)

        members = group.members.list()
        assert len(members) == no_of_members_before

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == no_of_shared_with_before - 1

        assert [sw["group_name"] for sw in shared_with] == [groups[0].name]

    def test__not_remove_groups_with_enforce_false(
        self, gl, group, users, groups, one_owner
    ):
        no_of_members_before = len(group.members.list())
        no_of_shared_with_before = len(gl.groups.get(group.id).shared_with_groups)

        setups = [
            # flag explicitly set to false
            f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  enforce: false
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
            """,
            # flag not set at all (but the default is false)
            f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
            """,
        ]
        for setup in setups:
            run_gitlabform(setup, group)

            members = group.members.list()
            assert len(members) == no_of_members_before

            members_usernames = {member.username for member in members}
            assert members_usernames == {
                f"{users[0].username}",
            }

            shared_with = gl.groups.get(group.id).shared_with_groups
            assert len(shared_with) == no_of_shared_with_before

    def test__change_group_access(self, gl, group, groups, users, one_owner):
        change_some_users_access = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              users:
                {users[0].username}:
                  access_level: {AccessLevel.OWNER.value}
              groups:
                {groups[0].full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
                {groups[1].full_path}:
                  group_access: {AccessLevel.OWNER.value}
        """

        run_gitlabform(change_some_users_access, group)

        shared_with = gl.groups.get(group.id).shared_with_groups
        for shared_with_group in shared_with:
            if shared_with_group["group_name"] == f"{groups[0]}":
                assert (
                    shared_with_group["group_access_level"]
                    == AccessLevel.DEVELOPER.value
                )
            if shared_with_group["group_name"] == f"{groups[1].full_path}":
                assert (
                    shared_with_group["group_access_level"] == AccessLevel.OWNER.value
                )

    def test__remove_all(self, gl, group, users, one_owner):
        no_shared_with = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              enforce: true
              users:
                {users[0].username}:
                  access_level: {AccessLevel.OWNER.value}
        """

        run_gitlabform(no_shared_with, group)

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 0

    def test__add_group_with_access_level_names(
        self, gl, group, users, groups, one_owner
    ):
        no_of_members_before = len(group.members.list())

        add_shared_with = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_members:
              users:
                {users[0].username}:
                  access_level: owner
              groups:
                {groups[0].full_path}:
                  group_access: developer
                {groups[1].full_path}:
                  group_access: developer
        """

        run_gitlabform(add_shared_with, group)

        members = group.members.list()
        assert len(members) == no_of_members_before, members

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 2

    def test__ignore_keep_bots_and_enforce(self, gl, group, users, groups, one_owner):
        no_of_members_before = len(group.members.list())

        add_shared_with = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  enforce: true
                  keep_bots: true
                  users:
                  {users[0].username}:
                    access_level: owner
                  groups:
                    {groups[0].full_path}:
                      group_access: developer
                    {groups[1].full_path}:
                      group_access: developer
            """

        run_gitlabform(add_shared_with, group)

        members = group.members.list()
        assert len(members) == no_of_members_before, members

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 2
