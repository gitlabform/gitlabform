import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    randomize_case,
)


@pytest.fixture(scope="class")
def two_members_in_other_group(gitlab, other_group, make_user):
    outsider_user1 = make_user(add_to_project=False)
    outsider_user2 = make_user(add_to_project=False)

    gitlab.add_member_to_group(
        other_group, outsider_user1.name, AccessLevel.OWNER.value
    )
    gitlab.add_member_to_group(
        other_group, outsider_user2.name, AccessLevel.DEVELOPER.value
    )

    yield [outsider_user1.name, outsider_user2.name]


class TestMembersCaseInsensitive:
    def test__user_case_insensitive(
        self, gitlab, group_and_project, three_members, outsider_user
    ):

        member1_name, _, _ = three_members

        change_user_level = f"""
        projects_and_groups:
          {group_and_project}:
            members:
              users:
                {randomize_case(member1_name)}: # refer to a user with a different case
                  access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(change_user_level, group_and_project)

    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__group_case_insensitive(
        self,
        gitlab,
        group_and_project,
        three_members,
        other_group,
        two_members_in_other_group,
    ):
        no_of_members_before = len(gitlab.get_project_members(group_and_project))
        no_of_members_of_other_group = len(gitlab.get_group_members(other_group))

        no_of_groups_shared_before = len(
            gitlab.get_shared_with_groups(group_and_project)
        )
        assert no_of_groups_shared_before == 0

        add_group = f"""
        projects_and_groups:
          {group_and_project}:
            members:
              groups:
                {randomize_case(other_group)}: # refer to a user with a different case
                  group_access: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(add_group, group_and_project)

        members = gitlab.get_project_members(group_and_project, all=True)

        assert len(members) == no_of_members_before + no_of_members_of_other_group

        for member in members:
            if member["username"] in two_members_in_other_group:
                # "group_access" is the *maximum* access level, see
                # https://docs.gitlab.com/ee/user/project/members/share_project_with_groups.html#maximum-access-level
                assert member["access_level"] <= AccessLevel.MAINTAINER.value

        no_of_groups_shared = len(gitlab.get_shared_with_groups(group_and_project))
        assert no_of_groups_shared == 1
