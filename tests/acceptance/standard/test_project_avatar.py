import os
import pytest
import tempfile
import shutil
from tests.acceptance import (
    run_gitlabform,
)


class TestProjectAvatar:
    def setup_method(self):
        # Use gitlabform logo
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        self.test_image_path = os.path.join(self.project_root, "docs/images/gitlabform-logo.png")

        # Check if the file exists
        assert os.path.exists(self.test_image_path), f"Test image not found at {self.test_image_path}"

    def test__project_avatar_set_absolute_path(self, project):
        # Test setting a project avatar with absolute path
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is set
        assert project.avatar_url is not None

    def test__project_avatar_paths_comprehensive(self, project):
        """Test both absolute and relative paths comprehensively"""

        # Test 1: Absolute path (already tested above, but included for completeness)
        config_absolute = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config_absolute, project)

        project = project.manager.get(project.id)
        assert project.avatar_url is not None

        # Test 2: Simple relative path
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Copy image to temp directory
            temp_image_name = "relative_test_avatar.png"
            shutil.copy2(self.test_image_path, temp_image_name)

            config_relative = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                project_settings:
                  avatar: "{temp_image_name}"
            """
            run_gitlabform(config_relative, project)

            project = project.manager.get(project.id)
            assert project.avatar_url is not None

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

        # Test 3: Relative path with subdirectory
        temp_dir2 = tempfile.mkdtemp()
        try:
            os.chdir(temp_dir2)

            subdir = "test_images"
            os.makedirs(subdir)
            relative_subdir_path = os.path.join(subdir, "subdir_avatar.png")
            shutil.copy2(self.test_image_path, relative_subdir_path)

            config_relative_subdir = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                project_settings:
                  avatar: "{relative_subdir_path}"
            """
            run_gitlabform(config_relative_subdir, project)

            project = project.manager.get(project.id)
            assert project.avatar_url is not None

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir2)

    def test__project_avatar_delete(self, project):
        # First ensure there's an avatar to delete by setting one
        config_set = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config_set, project)

        # Refresh project data to get current state
        project = project.manager.get(project.id)

        # Verify that avatar exists
        assert project.avatar_url is not None, "Avatar should exist after setting it"

        # Delete the avatar
        config_delete = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: ""
        """
        run_gitlabform(config_delete, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is removed
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__project_avatar_file_not_found_should_fail(self, project):
        # Test handling of non-existent avatar file path - should fail
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{nonexistent_path}"
        """

        # GitLabForm catches exceptions
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, project)

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

    def test__project_avatar_relative_file_not_found_should_fail(self, project):
        # Test handling of non-existent relative avatar file path - should fail
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Use non-existent relative path
            nonexistent_relative_path = "images/nonexistent_avatar.png"

            config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                project_settings:
                  avatar: "{nonexistent_relative_path}"
            """

            # Should fail with SystemExit since file won't be found
            with pytest.raises(SystemExit) as exc_info:
                run_gitlabform(config, project)

            # Verify it's the expected exit code for processing errors
            assert exc_info.value.code == 2

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

    def test__project_avatar_failure_with_other_settings(self, project):
        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should not be set due to avatar failure"

        # Store original description to verify it doesn't change
        original_project = project.manager.get(project.id)
        original_description = getattr(original_project, "description", "")

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
        """

        # Should fail due to avatar file not found
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, project)

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh project data and verify description wasn't changed
        updated_project = project.manager.get(project.id)
        current_description = getattr(updated_project, "description", "")

        # Description should remain unchanged since the process failed
        assert current_description == original_description
        assert current_description != test_description

    def test__project_avatar_other_settings_process_when_no_avatar_error(self, project):
        # Test that other settings are processed when there's no avatar error
        test_description = "Test description that should be set successfully"

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
              avatar: "{self.test_image_path}"
        """

        run_gitlabform(config, project)

        # Refresh project data
        updated_project = project.manager.get(project.id)

        # Both avatar and description should be set
        assert updated_project.avatar_url is not None
        assert getattr(updated_project, "description", "") == test_description
