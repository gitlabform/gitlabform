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
        self.test_image_absolute_path = os.path.join(self.project_root, "docs/images/gitlabform-logo.png")

        # Check if the file exists
        assert os.path.exists(self.test_image_absolute_path), f"Test image not found at {self.test_image_absolute_path}"

    def test__group_avatar_set_absolute_path(self, group):
        """Test setting a group avatar with absolute path"""
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{self.test_image_absolute_path}"
        """
        run_gitlabform(config, group)

        # Refresh group data
        group = group.manager.get(group.id)

        # Verify avatar is set
        assert group.avatar_url is not None

    def test__group_avatar_set_relative_path(self, group):
        """Test setting a group avatar with relative path"""
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Copy image to temp directory with relative name
            relative_image_name = "test_avatar.png"
            shutil.copy2(self.test_image_absolute_path, relative_image_name)

            config = f"""
            projects_and_groups:
              {group.full_path}/*:
                group_settings:
                  avatar: "{relative_image_name}"
            """
            run_gitlabform(config, group)

            group = group.manager.get(group.id)
            assert group.avatar_url is not None

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

    def test__group_avatar_delete(self, group):
        """Test deleting a group avatar"""
        # First set an avatar
        config_set = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{self.test_image_absolute_path}"
        """
        run_gitlabform(config_set, group)

        # Verify avatar exists
        group = group.manager.get(group.id)
        assert group.avatar_url is not None

        # Delete the avatar
        config_delete = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: ""
        """
        run_gitlabform(config_delete, group)

        # Verify avatar is removed
        group = group.manager.get(group.id)
        assert group.avatar_url is None or "gravatar" in group.avatar_url

    def test__group_avatar_delete_when_already_empty(self, group_for_function):
        """Test deleting avatar when it's already empty - should be no-op"""
        # Verify group has no custom avatar (fresh group)
        assert group_for_function.avatar_url is None or "gravatar" in group_for_function.avatar_url

        # Try to delete avatar when it's already empty
        config_delete_empty = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_settings:
              avatar: ""
        """
        run_gitlabform(config_delete_empty, group_for_function)

        # Verify nothing changed
        group_for_function = group_for_function.manager.get(group_for_function.id)
        assert group_for_function.avatar_url is None or "gravatar" in group_for_function.avatar_url

    def test__group_avatar_file_not_found_should_fail(self, group):
        """Test handling of non-existent avatar file path - should fail"""
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{nonexistent_path}"
        """

        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, group)

        assert exc_info.value.code == 2
