from unittest.mock import MagicMock, patch, call
import pytest
from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.project.project_security_settings import (
    ProjectSecuritySettingsProcessor,
)


class TestProjectSecuritySettingsProcessor:
    @pytest.fixture
    def mock_gitlab(self):
        """Create a mock GitLab instance"""
        gitlab = MagicMock()
        # Mock the session and gitlab_config attributes needed by GitlabWrapper
        gitlab.session = MagicMock()
        gitlab.gitlab_config = {
            "url": "http://localhost",
            "token": "test-token",
            "ssl_verify": True,
        }
        return gitlab

    @pytest.fixture
    def mock_gl(self):
        """Create a mock python-gitlab instance"""
        gl = MagicMock()
        return gl

    @pytest.fixture
    def mock_project(self):
        """Create a mock Project"""
        project = MagicMock(spec=Project)
        project.encoded_id = "123"
        project.id = 123
        return project

    @pytest.fixture
    def processor(self, mock_gitlab, mock_gl):
        """Create processor with mocked dependencies"""
        with patch(
            "gitlabform.processors.abstract_processor.GitlabWrapper"
        ) as mock_wrapper:
            mock_wrapper.return_value.get_gitlab.return_value = mock_gl
            processor = ProjectSecuritySettingsProcessor(mock_gitlab)
            return processor

    def test_init(self, mock_gitlab, mock_gl):
        """Test processor initialization"""
        with patch(
            "gitlabform.processors.abstract_processor.GitlabWrapper"
        ) as mock_wrapper:
            mock_wrapper.return_value.get_gitlab.return_value = mock_gl
            processor = ProjectSecuritySettingsProcessor(mock_gitlab)
            assert processor.configuration_name == "project_security_settings"
            assert processor.gitlab == mock_gitlab

    def test_get_project_security_settings_returns_dict(
        self, processor, mock_gl, mock_project
    ):
        """Test get_project_security_settings returns security settings"""
        # Setup
        mock_gl.get_project_by_path_cached.return_value = mock_project
        expected_settings = {
            "pre_receive_secret_detection_enabled": True,
            "security_training_enabled": False,
        }
        mock_gl.http_get.return_value = expected_settings

        # Execute
        result = processor.get_project_security_settings("test/project")

        # Assert
        assert result == expected_settings
        mock_gl.get_project_by_path_cached.assert_called_once_with("test/project")
        mock_gl.http_get.assert_called_once_with("/projects/123/security_settings")

    def test_get_project_security_settings_with_encoded_project_id(
        self, processor, mock_gl, mock_project
    ):
        """Test that encoded_id is used correctly in the API path"""
        # Setup
        mock_project.encoded_id = "test%2Fproject"
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = {"some_setting": True}

        # Execute
        processor.get_project_security_settings("test/project")

        # Assert
        mock_gl.http_get.assert_called_once_with(
            "/projects/test%2Fproject/security_settings"
        )

    def test_update_project_security_settings(
        self, processor, mock_gl, mock_project
    ):
        """Test updating project security settings"""
        # Setup
        settings = {
            "pre_receive_secret_detection_enabled": True,
            "security_training_enabled": True,
        }

        # Execute
        processor._update_project_security_settings(mock_project, settings)

        # Assert
        mock_gl.http_put.assert_called_once_with(
            "/projects/123/security_settings", post_data=settings
        )

    def test_process_configuration_when_update_needed(
        self, processor, mock_gl, mock_project
    ):
        """Test _process_configuration when settings need update"""
        # Setup
        configuration = {
            "project_security_settings": {
                "pre_receive_secret_detection_enabled": True,
            }
        }
        current_settings = {
            "pre_receive_secret_detection_enabled": False,
        }
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        # Execute
        processor._process_configuration("test/project", configuration)

        # Assert
        mock_gl.http_put.assert_called_once_with(
            "/projects/123/security_settings",
            post_data={"pre_receive_secret_detection_enabled": True},
        )

    def test_process_configuration_when_no_update_needed(
        self, processor, mock_gl, mock_project
    ):
        """Test _process_configuration when settings don't need update"""
        # Setup
        configuration = {
            "project_security_settings": {
                "pre_receive_secret_detection_enabled": True,
            }
        }
        current_settings = {
            "pre_receive_secret_detection_enabled": True,
            "some_other_setting": False,
        }
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        # Execute
        processor._process_configuration("test/project", configuration)

        # Assert - http_put should not be called when no update is needed
        mock_gl.http_put.assert_not_called()

    def test_process_configuration_with_multiple_settings(
        self, processor, mock_gl, mock_project
    ):
        """Test processing configuration with multiple security settings"""
        # Setup
        configuration = {
            "project_security_settings": {
                "pre_receive_secret_detection_enabled": True,
                "security_training_enabled": True,
                "auto_fix_enabled": False,
            }
        }
        current_settings = {
            "pre_receive_secret_detection_enabled": False,
            "security_training_enabled": False,
            "auto_fix_enabled": True,
        }
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        # Execute
        processor._process_configuration("test/project", configuration)

        # Assert
        mock_gl.http_put.assert_called_once_with(
            "/projects/123/security_settings",
            post_data={
                "pre_receive_secret_detection_enabled": True,
                "security_training_enabled": True,
                "auto_fix_enabled": False,
            },
        )

    def test_print_diff(self, processor, mock_gl, mock_project):
        """Test _print_diff method"""
        # Setup
        current_settings = {
            "pre_receive_secret_detection_enabled": False,
        }
        config_settings = {
            "pre_receive_secret_detection_enabled": True,
        }
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        with patch(
            "gitlabform.processors.project.project_security_settings.DifferenceLogger"
        ) as mock_diff_logger:
            # Execute
            processor._print_diff("test/project", config_settings, diff_only_changed=True)

            # Assert
            mock_diff_logger.log_diff.assert_called_once_with(
                "project_security_settings changes",
                current_settings,
                config_settings,
                only_changed=True,
            )

    def test_print_diff_with_diff_only_changed_false(
        self, processor, mock_gl, mock_project
    ):
        """Test _print_diff with diff_only_changed=False"""
        # Setup
        current_settings = {"setting1": True}
        config_settings = {"setting1": False}
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        with patch(
            "gitlabform.processors.project.project_security_settings.DifferenceLogger"
        ) as mock_diff_logger:
            # Execute
            processor._print_diff("test/project", config_settings, diff_only_changed=False)

            # Assert
            mock_diff_logger.log_diff.assert_called_once_with(
                "project_security_settings changes",
                current_settings,
                config_settings,
                only_changed=False,
            )

    def test_process_configuration_uses_correct_project_path(
        self, processor, mock_gl, mock_project
    ):
        """Test that correct project path is used throughout processing"""
        # Setup
        project_path = "my-group/my-subgroup/my-project"
        configuration = {
            "project_security_settings": {
                "pre_receive_secret_detection_enabled": True,
            }
        }
        current_settings = {"pre_receive_secret_detection_enabled": False}
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        # Execute
        processor._process_configuration(project_path, configuration)

        # Assert - project path should be used for getting project
        assert mock_gl.get_project_by_path_cached.call_count == 2
        mock_gl.get_project_by_path_cached.assert_has_calls(
            [call(project_path), call(project_path)]
        )

    def test_get_project_security_settings_http_get_returns_dict(
        self, processor, mock_gl, mock_project
    ):
        """Test that assertion passes when http_get returns dict"""
        # Setup
        mock_gl.get_project_by_path_cached.return_value = mock_project
        # http_get returns a dict (not Response)
        mock_gl.http_get.return_value = {"setting": "value"}

        # Execute - should not raise assertion error
        result = processor.get_project_security_settings("test/project")

        # Assert
        assert result == {"setting": "value"}

    def test_process_configuration_with_empty_settings(
        self, processor, mock_gl, mock_project
    ):
        """Test processing with empty security settings configuration"""
        # Setup
        configuration = {"project_security_settings": {}}
        current_settings = {"pre_receive_secret_detection_enabled": True}
        mock_gl.get_project_by_path_cached.return_value = mock_project
        mock_gl.http_get.return_value = current_settings

        # Execute
        processor._process_configuration("test/project", configuration)

        # Assert - should not call http_put with empty settings if no changes needed
        # The _needs_update check should handle this
        mock_gl.http_put.assert_not_called()
