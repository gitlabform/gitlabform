import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    randomize_case,
    allowed_codes,
)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(group, root_user, users):
    group.members.create({"user_id": users[0].id, "access_level": AccessLevel.OWNER.value})
    group.members.create({"user_id": users[1].id, "access_level": AccessLevel.DEVELOPER.value})
    group.members.create({"user_id": users[2].id, "access_level": AccessLevel.DEVELOPER.value})
    group.members.delete(root_user.id)

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    group.members.create({"user_id": root_user.id, "access_level": AccessLevel.OWNER.value})

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        with allowed_codes(404):
            group.members.delete(user.id)


@pytest.fixture(scope="function")
def one_owner(group, groups, subgroup, root_user, users):
    group.members.create({"user_id": users[0].id, "access_level": AccessLevel.OWNER.value})
    group.members.delete(root_user.id)

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    group.members.create({"user_id": root_user.id, "access_level": AccessLevel.OWNER.value})

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


class TestGroupMembersCaseInsensitive:
    def test__user_case_insensitive(self, group, users, one_owner_and_two_developers):
        no_of_members_before = len(group.members.list())
        user_to_add = f"{users[3].username}"

        add_users = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {randomize_case(users[0].username)}:
                      access_level: {AccessLevel.OWNER.value}
                    {randomize_case(users[1].username)}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {randomize_case(users[2].username)}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {randomize_case(user_to_add)}: # new user 1
                      access_level: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(add_users, group)

        members = group.members.list()
        assert len(members) == no_of_members_before + 1

        members_usernames = [member.username for member in members]
        assert members_usernames.count(user_to_add) == 1

    def test__group_case_insensitive(self, gl, group, users, groups, one_owner):
        no_of_members_before = len(group.members.list())

        add_shared_with = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_members:
                  users:
                    {users[0].username}:
                      access_level: {AccessLevel.OWNER.value}
                  groups:
                    {randomize_case(groups[0].full_path)}:
                      group_access: {AccessLevel.DEVELOPER.value}
                    {randomize_case(groups[1].full_path)}:
                      group_access: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(add_shared_with, group)

        members = group.members.list()
        assert len(members) == no_of_members_before, members

        shared_with = gl.groups.get(group.id).shared_with_groups
        assert len(shared_with) == 2
