import os
from tests.acceptance import (
    run_gitlabform,
)


class TestAvatar:
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
            project:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is set (avatar_url should not be None)
        assert project.avatar_url is not None

    def test__project_avatar_delete(self, project):
        # First set an avatar
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)
        assert project.avatar_url is not None

        # Then delete it
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project:
              avatar: ""
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is removed
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__group_avatar_set(self, group):
        # Test setting a group avatar
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, group)

        # Refresh group data
        group = group.manager.get(group.id)

        # Verify avatar is set
        assert group.avatar_url is not None

    def test__group_avatar_delete(self, group):
        # First set an avatar
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group:
              avatar: "{self.test_image_path}"
        """
        run_gitlabform(config, group)

        # Refresh group data
        group = group.manager.get(group.id)
        assert group.avatar_url is not None

        # Then delete it
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group:
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
            group:
              avatar: "{nonexistent_path}"
        """

        # This should run without crashing, even though the file doesn't exist
        run_gitlabform(config, group)

        # Refresh group data - avatar should remain unchanged since file wasn't found
        group_updated = group.manager.get(group.id)
        assert group_updated.avatar_url == original_avatar_url

    def test__group_avatar_no_group_config(self, group):
        # Test when group config is missing
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            # No 'group' section
            project:
              something_else: value
        """

        # Store original state
        group_original = group.manager.get(group.id)
        original_avatar_url = group_original.avatar_url

        # Run GitLabForm
        run_gitlabform(config, group)

        # Verify no changes to avatar (since group section was missing)
        group_updated = group.manager.get(group.id)
        assert group_updated.avatar_url == original_avatar_url

    def test__group_avatar_config_without_avatar(self, group):
        # Test when 'avatar' key is not in group config
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group:
              # No 'avatar' key
              description: "Test description for coverage"
        """

        # Store original state
        group_original = group.manager.get(group.id)
        original_avatar_url = group_original.avatar_url

        # Run GitLabForm
        run_gitlabform(config, group)

        # Verify no changes to avatar (since avatar key was missing)
        group_updated = group.manager.get(group.id)
        assert group_updated.avatar_url == original_avatar_url
