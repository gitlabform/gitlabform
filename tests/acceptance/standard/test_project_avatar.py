import os
import pytest
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

    def test__project_avatar_set(self, project):
        # Test setting a project avatar
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is set (avatar_url should not be None)
        assert project.avatar_url is not None

    def test__project_avatar_delete(self, project):
        # Refresh project data to get current state
        project = project.manager.get(project.id)

        # Verify that avatar exists (should be set by previous test)
        assert project.avatar_url is not None, "Avatar should exist from previous test"

        # Delete the avatar
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: ""
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is removed
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__avatar_file_not_found(self, project):
        # Test handling of non-existent avatar file path
        nonexistent_path = "/path/to/nonexistent/image.png"

        # Store the original avatar URL to verify it doesn't change
        project_original = project.manager.get(project.id)
        original_avatar_url = project_original.avatar_url

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{nonexistent_path}"
        """

        # This should run without crashing, even though the file doesn't exist
        run_gitlabform(config, project)

        # Refresh project data - avatar should remain unchanged since file wasn't found
        project_updated = project.manager.get(project.id)
        assert project_updated.avatar_url == original_avatar_url
