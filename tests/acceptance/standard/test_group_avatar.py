import os
import pytest
import tempfile
import shutil
from tests.acceptance import (
    run_gitlabform,
)


class TestGroupAvatar:
    def setup_method(self):
        # Use gitlabform logo
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        self.test_image_path = os.path.join(self.project_root, "docs/images/gitlabform-logo.png")

        # Check if the file exists
        assert os.path.exists(self.test_image_path), f"Test image not found at {self.test_image_path}"

    def test__group_avatar_set_absolute_path(self, group):
        # Test setting a group avatar with absolute path
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, group)

        # Refresh group data
        group = group.manager.get(group.id)

        # Verify avatar is set
        assert group.avatar_url is not None

    def test__group_avatar_paths_comprehensive(self, group):
        """Test both absolute and relative paths comprehensively"""

        # Test 1: Absolute path (already tested above, but included for completeness)
        config_absolute = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config_absolute, group)

        group = group.manager.get(group.id)
        assert group.avatar_url is not None

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
              {group.full_path}/*:
                group_settings:
                  avatar: "{temp_image_name}"
            """
            run_gitlabform(config_relative, group)

            group = group.manager.get(group.id)
            assert group.avatar_url is not None

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
              {group.full_path}/*:
                group_settings:
                  avatar: "{relative_subdir_path}"
            """
            run_gitlabform(config_relative_subdir, group)

            group = group.manager.get(group.id)
            assert group.avatar_url is not None

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir2)

    def test__group_avatar_delete(self, group):
        # First ensure there's an avatar to delete by setting one
        config_set = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config_set, group)

        # Refresh group data to get current state
        group = group.manager.get(group.id)

        # Verify that avatar exists
        assert group.avatar_url is not None, "Avatar should exist after setting it"

        # Delete the avatar
        config_delete = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: ""
        """
        run_gitlabform(config_delete, group)

        # Refresh group data
        group = group.manager.get(group.id)

        # Verify avatar is removed
        assert group.avatar_url is None or "gravatar" in group.avatar_url

    def test__group_avatar_file_not_found_should_fail(self, group):
        # Test handling of non-existent avatar file path - should fail
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{nonexistent_path}"
        """

        # GitLabForm catches exceptions
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, group)

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

    def test__group_avatar_relative_file_not_found_should_fail(self, group):
        # Test handling of non-existent relative avatar file path - should fail
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Use non-existent relative path
            nonexistent_relative_path = "images/nonexistent_avatar.png"

            config = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_settings:
                  avatar: "{nonexistent_relative_path}"
            """

            # Should fail with SystemExit since file won't be found
            with pytest.raises(SystemExit) as exc_info:
                run_gitlabform(config, group)

            # Verify it's the expected exit code for processing errors
            assert exc_info.value.code == 2

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

    def test__group_avatar_failure_with_other_settings(self, group):
        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should not be set due to avatar failure"

        # Store original description to verify it doesn't change
        original_group = group.manager.get(group.id)
        original_description = getattr(original_group, "description", "")

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
        """

        # Should fail due to avatar file not found
        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, group)

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh group data and verify description wasn't changed
        updated_group = group.manager.get(group.id)
        current_description = getattr(updated_group, "description", "")

        # Description should remain unchanged since the process failed
        assert current_description == original_description
        assert current_description != test_description

    def test__group_avatar_other_settings_process_when_no_avatar_error(self, group):
        # Test that other settings are processed when there's no avatar error
        test_description = "Test description that should be set successfully"

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              description: "{test_description}"
              avatar: "{self.test_image_path}"
        """

        run_gitlabform(config, group)

        # Refresh group data
        updated_group = group.manager.get(group.id)

        # Both avatar and description should be set
        assert updated_group.avatar_url is not None
        assert getattr(updated_group, "description", "") == test_description

    def test__group_avatar_delete_when_already_empty(self, group):
        """Test deleting avatar when it's already empty - should be no-op"""
        # First ensure the group has no avatar
        group = group.manager.get(group.id)

        # If there's an avatar, remove it first
        if group.avatar_url and "gravatar" not in group.avatar_url:
            config_remove = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_settings:
                  avatar: ""
            """
            run_gitlabform(config_remove, group)
            group = group.manager.get(group.id)

        # Store the current avatar state (should be None or gravatar)
        original_avatar_url = group.avatar_url

        # Try to delete avatar when it's already empty
        config_delete_empty = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: ""
        """
        run_gitlabform(config_delete_empty, group)

        # Refresh and verify nothing changed
        group = group.manager.get(group.id)
        assert group.avatar_url == original_avatar_url

    def test__group_avatar_generic_exception_handling(self, group):
        """Test generic exception handling during avatar upload"""

        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Create a directory with the name of an image file
            # This should cause an exception when trying to open it as a file
            fake_image_dir = "fake_image.png"
            os.makedirs(fake_image_dir)

            config = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_settings:
                  avatar: "{fake_image_dir}"
            """

            # Should fail with SystemExit due to the exception
            with pytest.raises(SystemExit) as exc_info:
                run_gitlabform(config, group)

            assert exc_info.value.code == 2

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)
