from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


class TestMembersEnforce:
    def test__enforce(
        self,
        gitlab,
        group_and_project,
        three_members,
        outsider_user,
    ):
        members_before = gitlab.get_project_members(group_and_project)
        assert len(members_before) > 0

        members_usernames_before = [member["username"] for member in members_before]
        assert outsider_user not in members_usernames_before

        enforce_users = f"""
            projects_and_groups:
              {group_and_project}:
                members:
                  users:
                    {outsider_user}: # new user
                      access_level: {AccessLevel.MAINTAINER.value}
                  enforce: true
            """

        run_gitlabform(enforce_users, group_and_project)

        members = gitlab.get_project_members(group_and_project)

        assert len(members) == 1
        assert members[0]["username"] == outsider_user
