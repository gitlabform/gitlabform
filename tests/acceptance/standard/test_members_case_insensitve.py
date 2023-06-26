import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    randomize_case,
)


@pytest.fixture(scope="class")
def two_members_in_other_group(other_group, make_user):
    outsider_user1 = make_user(add_to_project=False)
    outsider_user2 = make_user(add_to_project=False)

    other_group.members.create(
        {"access_level": AccessLevel.OWNER.value, "user_id": outsider_user1.id}
    )
    other_group.members.create(
        {"access_level": AccessLevel.DEVELOPER.value, "user_id": outsider_user2.id}
    )

    yield [outsider_user1, outsider_user2]


class TestMembersCaseInsensitive:
    def test__user_case_insensitive(self, project, three_members, outsider_user):
        no_of_members_before = len(project.members.list())

        change_user_level = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            members:
              users:
                {randomize_case(outsider_user.username)}: # refer to a user with a different case
                  access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(change_user_level, project)

        members = project.members.list()
        assert len(members) == no_of_members_before + 1

        members_usernames = [member.username for member in members]
        assert outsider_user.username in members_usernames

    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__group_case_insensitive(
        self,
        gl,
        project,
        three_members,
        other_group,
        two_members_in_other_group,
    ):
        no_of_members_before = len(project.members.list())
        no_of_members_of_other_group = len(other_group.members.list())

        no_of_groups_shared_before = len(gl.projects.get(project.id).shared_with_groups)
        assert no_of_groups_shared_before == 0

        add_group = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            members:
              groups:
                {randomize_case(other_group.full_path)}: # refer to a user with a different case
                  group_access: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(add_group, project)

        members = project.members_all.list()

        assert len(members) == no_of_members_before + no_of_members_of_other_group

        for member in members:
            if member.username in two_members_in_other_group:
                # "group_access" is the *maximum* access level, see
                # https://docs.gitlab.com/ee/user/project/members/share_project_with_groups.html#maximum-access-level
                assert member.access_level <= AccessLevel.MAINTAINER.value

        no_of_groups_shared = len(gl.projects.get(project.id).shared_with_groups)
        assert no_of_groups_shared == 1
