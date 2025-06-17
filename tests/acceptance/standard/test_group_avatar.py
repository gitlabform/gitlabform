import os
import pytest
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

    def test__group_avatar_set(self, group):
        # Test setting a group avatar
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

    def test__group_avatar_delete(self, group):
        # Refresh group data to get current state
        group = group.manager.get(group.id)

        # Verify that avatar exists (should be set by previous test)
        assert group.avatar_url is not None, "Avatar should exist from previous test"

        # Delete the avatar
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: ""
        """
        run_gitlabform(config, group)

        # Refresh group data
        group = group.manager.get(group.id)

        # Verify avatar is removed
        assert group.avatar_url is None or "gravatar" in group.avatar_url

    def test__group_avatar_file_not_found(self, group):
        # Test handling of non-existent avatar file path
        nonexistent_path = "/path/to/nonexistent/image.png"

        # Store the original avatar URL to verify it doesn't change
        group_original = group.manager.get(group.id)
        original_avatar_url = group_original.avatar_url

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{nonexistent_path}"
        """

        # This should run without crashing, even though the file doesn't exist
        run_gitlabform(config, group)

        # Refresh group data - avatar should remain unchanged since file wasn't found
        group_updated = group.manager.get(group.id)
        assert group_updated.avatar_url == original_avatar_url
