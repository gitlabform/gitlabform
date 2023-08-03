import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


@pytest.fixture(scope="function")
def bot_member(gl, make_project_access_token, project_for_function):
    token = make_project_access_token(target_project = project_for_function)

    bot_member = gl.users.get(token.user_id)

    yield bot_member

    token.delete()


class TestMembersEnforce:
    def test__enforce(
        self,
        project,
        three_members,
        outsider_user,
    ):
        members_before = project.members.list()
        assert len(members_before) == len(three_members)

        members_usernames_before = [member.username for member in members_before]
        assert outsider_user.username not in members_usernames_before

        enforce_users = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                members:
                  users:
                    {outsider_user.username}: # new user
                      access_level: {AccessLevel.MAINTAINER.value}
                  enforce: true
            """

        run_gitlabform(enforce_users, project)

        members = project.members.list()

        assert len(members) == 1
        assert members[0].username == outsider_user.username

    def test__enforce_keep_bots(
        self,
        project_for_function,
        bot_member,
        outsider_user,
    ):
        members_before = project_for_function.members.list()
        assert len(members_before) == 1

        members_usernames_before = [member.username for member in members_before]
        assert outsider_user.username not in members_usernames_before

        enforce_users = f"""
            projects_and_groups:
              {project_for_function.path_with_namespace}:
                members:
                  users:
                    {outsider_user.username}: # new user
                      access_level: {AccessLevel.MAINTAINER.value}
                  enforce: true
                  keep_bots: true
            """

        run_gitlabform(enforce_users, project_for_function)

        members = project_for_function.members.list()

        assert len(members) == 2
        assert members[0].username == bot_member.username
