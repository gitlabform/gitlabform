import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


class TestMembers:
    def test__add_user(self, project, three_members, outsider_user):
        members_before = project.members.list()
        assert len(members_before) > 0

        members_usernames_before = [member.username for member in members_before]
        assert outsider_user.username not in members_usernames_before

        add_users = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            members:
              users:
                {outsider_user.username}: # new user
                  access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(add_users, project)

        members = project.members.list()
        assert len(members) == len(members_before) + 1

        members_usernames = [member.username for member in members]
        assert outsider_user.username in members_usernames

    def test__no_groups_and_no_users(self, project):

        config_with_error = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            members:
              # there should be a sub-key 'users' here, not directly a user
              some_user1: 
                access_level: {AccessLevel.DEVELOPER.value}
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config_with_error, project)

    def test__add_user_with_access_level_names(
        self, project, three_members, outsider_user
    ):
        members_before = project.members.list()
        assert len(members_before) > 0

        members_usernames_before = [member.username for member in members_before]
        assert outsider_user.username not in members_usernames_before

        add_users = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                members:
                  users:
                    {outsider_user.username}: # new user
                      access_level: maintainer
            """

        run_gitlabform(add_users, project)

        members = project.members.list()
        assert len(members) == len(members_usernames_before) + 1

        members_usernames = [member.username for member in members]
        assert outsider_user.username in members_usernames
