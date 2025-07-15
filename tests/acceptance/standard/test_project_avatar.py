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
        self.test_image_absolute_path = os.path.join(self.project_root, "docs/images/gitlabform-logo.png")

        # Check if the file exists
        assert os.path.exists(self.test_image_absolute_path), f"Test image not found at {self.test_image_absolute_path}"

    def test__project_avatar_set_absolute_path(self, project):
        """Test setting a project avatar with absolute path"""
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_absolute_path}"
        """
        run_gitlabform(config, project)

        # Refresh project data
        project = project.manager.get(project.id)

        # Verify avatar is set
        assert project.avatar_url is not None

    def test__project_avatar_set_relative_path(self, project):
        """Test setting a project avatar with relative path"""
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Copy image to temp directory with relative name
            relative_image_name = "test_avatar.png"
            shutil.copy2(self.test_image_absolute_path, relative_image_name)

            config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                project_settings:
                  avatar: "{relative_image_name}"
            """
            run_gitlabform(config, project)

            project = project.manager.get(project.id)
            assert project.avatar_url is not None

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

    def test__project_avatar_delete(self, project):
        """Test deleting a project avatar"""
        # First set an avatar
        config_set = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{self.test_image_absolute_path}"
        """
        run_gitlabform(config_set, project)

        # Verify avatar exists
        project = project.manager.get(project.id)
        assert project.avatar_url is not None

        # Delete the avatar
        config_delete = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: ""
        """
        run_gitlabform(config_delete, project)

        # Verify avatar is removed
        project = project.manager.get(project.id)
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__project_avatar_delete_when_already_empty(self, project_for_function):
        """Test deleting avatar when it's already empty - should be no-op"""
        # Verify project has no custom avatar (fresh project)
        assert project_for_function.avatar_url is None or "gravatar" in project_for_function.avatar_url

        # Try to delete avatar when it's already empty
        config_delete_empty = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            project_settings:
              avatar: ""
        """
        run_gitlabform(config_delete_empty, project_for_function)

        # Verify nothing changed
        project_for_function = project_for_function.manager.get(project_for_function.id)
        assert project_for_function.avatar_url is None or "gravatar" in project_for_function.avatar_url

    def test__project_avatar_file_not_found_should_fail(self, project):
        """Test handling of non-existent avatar file path - should fail"""
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{nonexistent_path}"
        """

        with pytest.raises(SystemExit) as exc_info:
            run_gitlabform(config, project)

        assert exc_info.value.code == 2
