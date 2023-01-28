from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


class TestMembersEnforce:
    def test__enforce(
        self,
        project,
        three_members,
        outsider_user,
    ):
        members_before = project.members.list()
        assert len(members_before) > 0

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
