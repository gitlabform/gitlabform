import logging

import pytest

from gitlabform import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_ultimate_license


class TestGroupMembers:
    def test__add_group_to_group_members_with_custom_role_by_id(self, gl, group_for_function, groups, random_string):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        add_group = f"""
              projects_and_groups:
                {group_for_function.full_path}/*:
                  group_members:
                    groups:
                      {groups[0].full_path}:
                        group_access: {base_access_level}
                        member_role: {member_role_id}
              """

        run_gitlabform(add_group, group_for_function)
        run_gitlabform(add_group, group_for_function)

        shared_with_groups = gl.groups.get(group_for_function.id).shared_with_groups
        shared_group = next(group for group in shared_with_groups if group["group_id"] == groups[0].id)
        assert shared_group["group_access_level"] == base_access_level
        assert shared_group["member_role_id"] == member_role_id

    def test__add_user_to_group_members_with_custom_role_by_id(self, gl, group_for_function, users, random_string):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        add_users = f"""
              projects_and_groups:
                {group_for_function.full_path}/*:
                  group_members:
                    users:
                      {users[0].username}:
                        access_level: {base_access_level}
                        member_role: {member_role_id}
              """

        run_gitlabform(add_users, group_for_function)

        members = group_for_function.members.list(get_all=True)
        assert len(members) == 2

        member = members[1]
        assert member.username == users[0].username
        assert member.access_level == base_access_level
        assert member.get_id() == users[0].get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__add_user_to_group_members_with_custom_role_by_name(self, gl, group_for_function, users, random_string):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        add_users = f"""
              projects_and_groups:
                {group_for_function.full_path}/*:
                  group_members:
                    users:
                      {users[0].username}:
                        access_level: {base_access_level}
                        member_role: {random_string}
              """

        run_gitlabform(add_users, group_for_function)

        members = group_for_function.members.list(get_all=True)
        assert len(members) == 2

        member = members[1]
        assert member.username == users[0].username
        assert member.access_level == base_access_level
        assert member.get_id() == users[0].get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__can_add_user_to_group_members_with_custom_role_by_name_is_not_case_sensitive(
        self, gl, group_for_function, users, random_string
    ):
        base_access_level = AccessLevel.REPORTER.value
        member_role_id = self._create_custom_role(gl, base_access_level, random_string)

        add_users = f"""
                projects_and_groups:
                  {group_for_function.full_path}/*:
                    group_members:
                      users:
                        {users[0].username}:
                          access_level: {base_access_level}
                          member_role: {random_string.lower()}
                """

        run_gitlabform(add_users, group_for_function)

        members = group_for_function.members.list(get_all=True)
        assert len(members) == 2

        member = members[1]
        assert member.username == users[0].username
        assert member.access_level == base_access_level
        assert member.get_id() == users[0].get_id()
        assert member.member_role["id"] == member_role_id
        assert member.member_role["base_access_level"] == base_access_level

    def test__cannot_add_user_to_group_members_with_custom_role_where_custom_role_does_not_exist(
        self, gl, group_for_function, users, random_string, caplog
    ):
        base_access_level = AccessLevel.REPORTER.value

        add_users = f"""
                projects_and_groups:
                  {group_for_function.full_path}/*:
                    group_members:
                      users:
                        {users[0].username}:
                          access_level: {base_access_level}
                          member_role: {random_string.lower()}
                """

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exception:
                run_gitlabform(add_users, group_for_function)

        assert exception.type == SystemExit
        assert exception.value.code == EXIT_PROCESSING_ERROR
        assert f"Member Role with name or id {random_string} could not be found" in caplog.text

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
