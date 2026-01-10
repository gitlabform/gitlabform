import pytest
from unittest.mock import patch, MagicMock


class TestGitLabCoreRetryConfiguration:
    """
    Tests for GitLabCore retry configuration.
    Ensures that retry settings (max_retries, backoff_factor, retry_transient_errors)
    are correctly applied to the requests session.
    """

    @patch("gitlabform.gitlab.core.requests.Session")
    @patch("gitlabform.gitlab.core.Configuration")
    def test_default_retry_configuration(self, mock_configuration, mock_session):
        """Test that default retry configuration values are applied"""
        mock_configuration.return_value.get.return_value = {}
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Capture the HTTPAdapter instances passed to mount
        mounted_adapters = {}

        def capture_mount(url, adapter):
            mounted_adapters[url] = adapter

        mock_session_instance.mount.side_effect = capture_mount

        # Import here to apply patches
        from gitlabform.gitlab.core import GitLabCore

        with patch.object(GitLabCore, "_make_requests_to_api") as mock_api:
            mock_api.side_effect = [
                {"version": "16.0.0", "revision": "abc123"},
                {"username": "test_user", "is_admin": True},
            ]
            core = GitLabCore(config_string="gitlab:\n  url: https://gitlab.example.com\n  token: test-token")

        # Verify default values in gitlab_config
        assert core.gitlab_config["max_retries"] == 3
        assert core.gitlab_config["backoff_factor"] == pytest.approx(0.25)
        assert core.gitlab_config["retry_transient_errors"] is True

    @patch("gitlabform.gitlab.core.requests.Session")
    @patch("gitlabform.gitlab.core.Configuration")
    def test_custom_retry_configuration(self, mock_configuration, mock_session):
        """Test that custom retry configuration values are applied"""
        mock_configuration.return_value.get.return_value = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,
            "backoff_factor": 0.5,
            "retry_transient_errors": False,
        }
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        from gitlabform.gitlab.core import GitLabCore

        with patch.object(GitLabCore, "_make_requests_to_api") as mock_api:
            mock_api.side_effect = [
                {"version": "16.0.0", "revision": "abc123"},
                {"username": "test_user", "is_admin": True},
            ]
            core = GitLabCore()

        # Verify custom values in gitlab_config
        assert core.gitlab_config["max_retries"] == 5
        assert core.gitlab_config["backoff_factor"] == pytest.approx(0.5)
        assert core.gitlab_config["retry_transient_errors"] is False

    @patch("gitlabform.gitlab.core.HTTPAdapter")
    @patch("gitlabform.gitlab.core.Retry")
    @patch("gitlabform.gitlab.core.requests.Session")
    @patch("gitlabform.gitlab.core.Configuration")
    def test_retry_transient_errors_enabled_by_default(
        self, mock_configuration, mock_session, mock_retry, mock_http_adapter
    ):
        """Test that retry_transient_errors is enabled by default and includes 429 status code"""
        mock_configuration.return_value.get.return_value = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        from gitlabform.gitlab.core import GitLabCore

        with patch.object(GitLabCore, "_make_requests_to_api") as mock_api:
            mock_api.side_effect = [
                {"version": "16.0.0", "revision": "abc123"},
                {"username": "test_user", "is_admin": True},
            ]
            _ = GitLabCore()

        # Check that Retry was called with the expected status_forcelist including 429
        retry_call_kwargs = mock_retry.call_args.kwargs
        expected_status_forcelist = [429, 500, 502, 503, 504] + list(range(520, 531))
        assert retry_call_kwargs["status_forcelist"] == expected_status_forcelist

    @patch("gitlabform.gitlab.core.HTTPAdapter")
    @patch("gitlabform.gitlab.core.Retry")
    @patch("gitlabform.gitlab.core.requests.Session")
    @patch("gitlabform.gitlab.core.Configuration")
    def test_config_passed_to_retry(self, mock_configuration, mock_session, mock_retry, mock_http_adapter):
        """Test that max_retries value is correctly passed to Retry"""
        mock_configuration.return_value.get.return_value = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 10,
            "backoff_factor": 0.1,
            "retry_transient_errors": False,
        }
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        from gitlabform.gitlab.core import GitLabCore

        with patch.object(GitLabCore, "_make_requests_to_api") as mock_api:
            mock_api.side_effect = [
                {"version": "16.0.0", "revision": "abc123"},
                {"username": "test_user", "is_admin": True},
            ]
            _ = GitLabCore()

        # Check that Retry was called with the correct max_retries value
        retry_call_kwargs = mock_retry.call_args.kwargs
        assert retry_call_kwargs["total"] == 10
        assert retry_call_kwargs["backoff_factor"] == pytest.approx(0.1)
        assert retry_call_kwargs["status_forcelist"] == []
