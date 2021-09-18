import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


@pytest.fixture(scope="function")
def one_maintainer_and_two_developers(gitlab, group, project, users):
    group_and_project = f"{group}/{project}"

    gitlab.add_member_to_project(
        group_and_project, users[0], AccessLevel.MAINTAINER.value
    )
    gitlab.add_member_to_project(
        group_and_project, users[1], AccessLevel.DEVELOPER.value
    )
    gitlab.add_member_to_project(
        group_and_project, users[2], AccessLevel.DEVELOPER.value
    )

    yield group_and_project

    # we try to remove all users, not just the 3 added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_project(group_and_project, user)


@pytest.fixture(scope="function")
def other_group_with_users(gitlab, other_group, other_users):
    gitlab.add_member_to_group(other_group, other_users[0], AccessLevel.OWNER.value)
    gitlab.add_member_to_group(other_group, other_users[1], AccessLevel.DEVELOPER.value)
    gitlab.remove_member_from_group(other_group, "root")

    # TODO: make it nicer than a duplicated list of users from above
    yield other_group, [other_users[0], other_users[1]]

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.
    gitlab.add_member_to_group(other_group, "root", AccessLevel.OWNER.value)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in other_users:
        gitlab.remove_member_from_group(other_group, user)


class TestMembers:
    def test__add_user(
        self, gitlab, group, project, users, one_maintainer_and_two_developers
    ):
        group_and_project = f"{group}/{project}"
        members_before = gitlab.get_project_members(group_and_project)
        no_of_members_before = len(members_before)
        members_usernames_before = [member["username"] for member in members_before]

        user_to_add = users[3]
        assert user_to_add not in members_usernames_before

        add_users = f"""
        projects_and_groups:
          {group}/{project}:
            members:
              users:
                {user_to_add}: # new user
                  access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(add_users, group_and_project)

        members = gitlab.get_project_members(group_and_project)
        assert len(members) == no_of_members_before + 1

        members_usernames = [member["username"] for member in members]
        assert user_to_add in members_usernames

    # TODO: fix flaky test
    @pytest.mark.xfail(strict=False)
    def test__add_group(
        self,
        gitlab,
        group,
        project,
        one_maintainer_and_two_developers,
        other_group_with_users,
    ):
        group_and_project = f"{group}/{project}"
        other_group, other_group_users = other_group_with_users

        no_of_members_before = len(gitlab.get_project_members(group_and_project))
        no_of_members_of_group = len(other_group_users)

        # print(f"members before = {gitlab.get_project_members(group_and_project)}")
        # print(f"members of the group = {other_group_users}")

        no_of_groups_shared_before = len(
            gitlab.get_shared_with_groups(group_and_project)
        )
        assert no_of_groups_shared_before == 0

        add_group = f"""
        projects_and_groups:
          {group}/{project}:
            members:
              groups:
                {other_group}:
                  group_access: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(add_group, group_and_project)

        members = gitlab.get_project_members(group_and_project, all=True)

        # TODO: the +1 is for root, but actually why is that user inherited here?
        assert len(members) == no_of_members_before + no_of_members_of_group + 1

        for member in members:
            if member["username"] in other_group_users:
                # "group_access" is the *maximum* access level, see
                # https://docs.gitlab.com/ee/user/project/members/share_project_with_groups.html#maximum-access-level
                assert member["access_level"] <= AccessLevel.MAINTAINER.value

        no_of_groups_shared = len(gitlab.get_shared_with_groups(group_and_project))
        assert no_of_groups_shared == 1

    def test__no_groups_and_no_users(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        config_with_error = f"""
        projects_and_groups:
          {group}/{project}:
            members:
              # there should be a sub-key 'users' here, not directly a user
              {project}_user1: 
                access_level: {AccessLevel.DEVELOPER.value}
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config_with_error, group_and_project)
