import pytest

from gitlabform import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


class TestMembers:

    def test__add_user_to_project_with_custom_role_by_id(
        self, gl, group, project_for_function, outsider_user, random_string
    ):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
           projects_and_groups:
             {project_for_function.path_with_namespace}:
               members:
                 users:
                   {outsider_user.username}: # new user
                     access_level: {base_access_level}
                     member_role: {member_role_id}
           """

        run_gitlabform(add_users, project_for_function)

        members = project_for_function.members.list()
        assert len(members) == 1

        member = members[0]
        assert member.username == outsider_user.username
        assert member.access_level == base_access_level
        assert member.get_id() == outsider_user.get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__add_user_to_project_with_custom_role_by_name(
        self, gl, group, project_for_function, outsider_user, random_string
    ):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
           projects_and_groups:
             {project_for_function.path_with_namespace}:
               members:
                 users:
                   {outsider_user.username}: # new user
                     access_level: {base_access_level}
                     member_role: {random_string}
           """

        run_gitlabform(add_users, project_for_function)

        members = project_for_function.members.list()
        assert len(members) == 1

        member = members[0]
        assert member.username == outsider_user.username
        assert member.access_level == base_access_level
        assert member.get_id() == outsider_user.get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__adding_user_to_project_with_custom_role_by_name_is_not_case_sensitive(
        self, gl, group, project_for_function, outsider_user, random_string
    ):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
             projects_and_groups:
               {project_for_function.path_with_namespace}:
                 members:
                   users:
                     {outsider_user.username}: # new user
                       access_level: {base_access_level}
                       member_role: {random_string.upper()}
             """

        run_gitlabform(add_users, project_for_function)

        members = project_for_function.members.list()
        assert len(members) == 1

        member = members[0]
        assert member.username == outsider_user.username
        assert member.access_level == base_access_level
        assert member.get_id() == outsider_user.get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__cannot_add_user_to_project_with_custom_role_where_custom_role_does_not_exist(
        self, gl, group, project_for_function, outsider_user, random_string, capsys
    ):
        base_access_level = AccessLevel.REPORTER.value

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
           projects_and_groups:
             {project_for_function.path_with_namespace}:
               members:
                 users:
                   {outsider_user.username}: # new user
                     access_level: {base_access_level}
                     member_role: {random_string}
           """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(add_users, project_for_function)

        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert f"Member Role with name or id {random_string} could not be found" in captured.err

    def test__cannot_add_user_to_project_with_different_access_than_base_custom_role(
        self, gl, group, project_for_function, outsider_user, random_string, capsys
    ):
        base_access_level = AccessLevel.MAINTAINER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
           projects_and_groups:
             {project_for_function.path_with_namespace}:
               members:
                 users:
                   {outsider_user.username}: # new user
                     access_level: {AccessLevel.REPORTER.value}
                     member_role: {member_role_id}
           """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(add_users, project_for_function)

        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert "the custom role's base access level does not match the current access level" in captured.err

    def test__cannot_add_user_to_project_with_custom_role_but_no_access_level(
        self, gl, group, project_for_function, outsider_user, random_string, capsys
    ):
        base_access_level = AccessLevel.MAINTAINER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        members_before = project_for_function.members.list()
        assert len(members_before) == 0

        add_users = f"""
           projects_and_groups:
             {project_for_function.path_with_namespace}:
               members:
                 users:
                   {outsider_user.username}: # new user
                     member_role: {member_role_id}
           """

        with pytest.raises(SystemExit) as exception:
            run_gitlabform(add_users, project_for_function)

        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        captured = capsys.readouterr()
        assert "the custom role's base access level does not match the current access level" in captured.err

    def _create_custom_role(self, gl, base_access_level, random_string):
        # Python-Gitlab does not directly support Member Roles
        # - we can use https://python-gitlab.readthedocs.io/en/stable/api-levels.html#lower-level-api-http-methods
        # to invoke instance-level REST API:
        # https://docs.gitlab.com/ee/update/deprecations.html#deprecate-custom-role-creation-for-group-owners-on-self-managed
        member_role_data = {
            "name": random_string,
            "base_access_level": base_access_level,
            "read_code": "true",
        }
        path = f"/member_roles"
        response = gl.http_post(path, post_data=member_role_data)

        return response["id"]
