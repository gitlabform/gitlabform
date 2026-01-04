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
    Tests for GitlabWrapper kwargs filtering.
    Ensures that only valid parameters are passed to python-gitlab's Gitlab client
    and GraphQL client, preventing TypeError from unsupported kwargs.
    """

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_max_retries_not_passed_to_gitlab_client(self, mock_python_gitlab, mock_graphql):
        """Test that max_retries is NOT passed to PythonGitlab (would cause TypeError)"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,  # This should NOT be passed to PythonGitlab
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert "max_retries" not in call_kwargs

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_max_retries_passed_to_graphql_client(self, mock_python_gitlab, mock_graphql):
        """Test that max_retries IS passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_graphql.call_args.kwargs
        assert call_kwargs["max_retries"] == 5

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_only_valid_gitlab_client_params_passed(self, mock_python_gitlab, mock_graphql):
        """Test that only valid Gitlab client parameters are passed"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "ssl_verify": True,
            "timeout": 10,
            "max_retries": 5,  # GraphQL only
            "obey_rate_limit": True,  # GraphQL only
            "some_unknown_param": "value",  # Should be filtered out
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs

        # Valid params should be present
        assert call_kwargs["url"] == "https://gitlab.example.com"
        assert call_kwargs["private_token"] == "test-token"
        assert call_kwargs["ssl_verify"] is True
        assert call_kwargs["timeout"] == 10

        # Invalid params should NOT be present
        assert "max_retries" not in call_kwargs
        assert "obey_rate_limit" not in call_kwargs
        assert "some_unknown_param" not in call_kwargs

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_graphql_params_passed_correctly(self, mock_python_gitlab, mock_graphql):
        """Test that GraphQL-specific parameters are passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,
            "obey_rate_limit": False,
            "retry_transient_errors": True,
            "timeout": 30,
            "ssl_verify": False,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_graphql.call_args.kwargs

        assert call_kwargs["max_retries"] == 5
        assert call_kwargs["obey_rate_limit"] is False
        assert call_kwargs["retry_transient_errors"] is True
        assert call_kwargs["timeout"] == 30
        assert call_kwargs["ssl_verify"] is False

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_token_renamed_to_private_token(self, mock_python_gitlab, mock_graphql):
        """Test that 'token' config key is renamed to 'private_token' for Gitlab client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "my-secret-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs

        assert "token" not in call_kwargs
        assert call_kwargs["private_token"] == "my-secret-token"

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_retry_transient_errors_default_true(self, mock_python_gitlab, mock_graphql):
        """Test that retry_transient_errors defaults to True for Gitlab client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert call_kwargs["retry_transient_errors"] is True

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_retry_transient_errors_can_be_overridden(self, mock_python_gitlab, mock_graphql):
        """Test that retry_transient_errors can be overridden from config"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "retry_transient_errors": False,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert call_kwargs["retry_transient_errors"] is False

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_graphql_url_and_token_passed(self, mock_python_gitlab, mock_graphql):
        """Test that URL and token are passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        mock_graphql.assert_called_once()
        call_args = mock_graphql.call_args
        assert call_args.kwargs["url"] == "https://gitlab.example.com"
        assert call_args.kwargs["token"] == "test-token"
