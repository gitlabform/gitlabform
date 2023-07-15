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


class TestProjectMembersCaseInsensitive:
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
