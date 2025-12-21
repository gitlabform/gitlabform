import pytest
from gitlab import GitlabGetError

from gitlabform.gitlab.python_gitlab import PythonGitlab
from gitlabform.gitlab import GitlabWrapper, GitLab
from unittest.mock import MagicMock, patch


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


class TestGitlabWrapperExtraKwargs:
    """
    Tests for extra kwargs support in GitlabWrapper that should be passed to PythonGitlab.
    This includes retry_transient_errors, obey_rate_limit, and any other additional parameters
    defined in the configuration.
    """

    @patch("gitlabform.gitlab.PythonGitlab")
    def test_extra_kwargs_are_passed_to_python_gitlab(self, mock_python_gitlab):
        """Test that extra kwargs from config are passed to PythonGitlab initialization"""
        # Setup mock GitLab object with extra config parameters
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "ssl_verify": True,
            "timeout": 10,
            "retry_transient_errors": True,
            "obey_rate_limit": True,
            "foo": "bar",  # extra param for testing
        }

        # Create wrapper
        _ = GitlabWrapper(mock_gitlab)

        # Verify PythonGitlab was called with the correct arguments
        mock_python_gitlab.assert_called_once()
        call_kwargs = mock_python_gitlab.call_args.kwargs

        # Check standard parameters
        assert call_kwargs["url"] == "https://gitlab.example.com"
        assert call_kwargs["private_token"] == "test-token"
        assert call_kwargs["ssl_verify"] is True
        assert call_kwargs["timeout"] == 10
        assert call_kwargs["api_version"] == "4"

        # Check extra kwargs are passed
        assert call_kwargs["retry_transient_errors"] is True
        assert call_kwargs["obey_rate_limit"] is True
        assert call_kwargs["foo"] == "bar"

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_default_values_for_gitlab_config(self, mock_python_gitlab, mock_graphql):
        """Test that when only standard keys are provided, default values are used for others"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs

        print(call_kwargs)
        # Verify standard keys are passed directly as named parameters with defaults for others
        assert call_kwargs["url"] == "https://gitlab.example.com"
        assert call_kwargs["private_token"] == "test-token"
        assert call_kwargs["retry_transient_errors"] is True  # default value of kwarg

        # Verify no extra kwargs beyond the expected parameters
        expected_keys = {"url", "private_token", "retry_transient_errors", "api_version", "graphql", "session"}
        actual_keys = set(call_kwargs.keys())
        extra_keys = actual_keys - expected_keys

        # Only extra keys should be those not in excluded_keys (should be empty in this case)
        assert len(extra_keys) == 0
