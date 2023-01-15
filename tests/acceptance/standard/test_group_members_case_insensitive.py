import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    randomize_case,
)


@pytest.fixture(scope="function")
def one_owner_and_two_developers(gitlab, group, users):

    gitlab.add_member_to_group(group, users[0], AccessLevel.OWNER.value)
    gitlab.add_member_to_group(group, users[1], AccessLevel.DEVELOPER.value)
    gitlab.add_member_to_group(group, users[2], AccessLevel.DEVELOPER.value)
    gitlab.remove_member_from_group(group, "root")

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    gitlab.add_member_to_group(group, "root", AccessLevel.OWNER.value)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_group(group, user)


@pytest.fixture(scope="function")
def one_owner(gitlab, group, groups, subgroup, users):

    gitlab.add_member_to_group(group, users[0], AccessLevel.OWNER.value)
    gitlab.remove_member_from_group(group, "root")

    yield group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    gitlab.add_member_to_group(group, "root", AccessLevel.OWNER.value)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_group(group, user)

    gitlab.remove_share_from_group(group, subgroup)
    for share_with in groups:
        gitlab.remove_share_from_group(group, share_with)


class TestGroupMembersCaseInsensitive:
    def test__user_case_insensitive(
        self, gitlab, group, users, one_owner_and_two_developers
    ):

        no_of_members_before = len(gitlab.get_group_members(group))
        user_to_add = f"{users[3]}"

        add_users = f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  users:
                    {randomize_case(users[0])}:
                      access_level: {AccessLevel.OWNER.value}
                    {randomize_case(users[1])}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {randomize_case(users[2])}:
                      access_level: {AccessLevel.DEVELOPER.value}
                    {randomize_case(user_to_add)}: # new user 1
                      access_level: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(add_users, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before + 1

        members_usernames = [member["username"] for member in members]
        assert members_usernames.count(user_to_add) == 1

    def test__group_case_insensitive(self, gitlab, group, users, groups, one_owner):
        no_of_members_before = len(gitlab.get_group_members(group))

        add_shared_with = f"""
            projects_and_groups:
              {group}/*:
                group_members:
                  users:
                    {users[0]}:
                      access_level: {AccessLevel.OWNER.value}
                  groups:
                    {randomize_case(groups[0])}:
                      group_access: {AccessLevel.DEVELOPER.value}
                    {randomize_case(groups[1])}:
                      group_access: {AccessLevel.DEVELOPER.value}
            """

        run_gitlabform(add_shared_with, group)

        members = gitlab.get_group_members(group)
        assert len(members) == no_of_members_before, members

        shared_with = gitlab.get_group_shared_with(group)
        assert len(shared_with) == 2
