import pytest
from gitlab import GitlabGetError

from gitlabform.gitlab.python_gitlab import PythonGitlab
from unittest.mock import MagicMock


class TestPythonGitlab:

    def test_get_member_role_id_cached_gets_role_id_from_roles_in_group_on_saas(self):
        group_name = "Test"
        role_name = "custom_role"
        member_role_id = "1"

        python_gitlab = PythonGitlab(MagicMock())
        # Don't make a real GraphQl call
        python_gitlab._get_member_roles_from_group_cached = MagicMock(
            return_value=[dict(id=member_role_id, name=role_name)]
        )

        # Return we are in GitLab SaaS
        python_gitlab._is_gitlab_saas = MagicMock(return_value=True)

        role_id = python_gitlab.get_member_role_id_cached(role_name, group_name)

        python_gitlab._get_member_roles_from_group_cached.assert_called_with(group_name)
        assert role_id == int(member_role_id)

    def test_get_member_role_id_cached_gets_role_id_from_roles_on_instance_on_self_hosted(
        self,
    ):
        group_name = "Test"
        role_name = "custom_role_two"
        member_role_id = "5"

        python_gitlab = PythonGitlab(MagicMock())
        # Don't make a real GraphQl call
        python_gitlab._get_member_roles_from_instance_cached = MagicMock(
            return_value=[dict(id=member_role_id, name=role_name)]
        )

        # Return we are in GitLab SaaS
        python_gitlab._is_gitlab_saas = MagicMock(return_value=False)

        role_id = python_gitlab.get_member_role_id_cached(role_name, group_name)

        python_gitlab._get_member_roles_from_instance_cached.assert_called()
        assert role_id == int(member_role_id)

    def test_convert_result_to_member_roles_removes_GitlabGraphQl_specific_prefix_from_member_role_id(
        self,
    ):
        role_name = "custom_role"
        member_role_id = "1"

        member_role_id_prefix = "gid://gitlab/MemberRole/"

        member_role_nodes = [dict(id=f"{member_role_id_prefix}{member_role_id}", name=role_name)]

        python_gitlab = PythonGitlab(MagicMock())

        member_roles = python_gitlab._convert_result_to_member_roles(member_role_nodes)

        expected = [dict(id=member_role_id, name=role_name)]
        assert member_roles == expected
