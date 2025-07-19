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

    def test__project_avatar_file_not_found_continues_with_warning(self, project):
        """Test that non-existent avatar file shows warning but continues processing"""
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "{nonexistent_path}"
        """

        # Should not fail - avatar failure is now handled with warning
        run_gitlabform(config, project)

        # Avatar should remain unchanged (not set due to failure)
        project = project.manager.get(project.id)
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__project_avatar_no_avatar_config(self, project):
        """Test that no avatar config is handled gracefully"""
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              description: "Test without avatar config"
        """

        # Should work fine without avatar config
        run_gitlabform(config, project)

        # Verify other settings are applied
        project = project.manager.get(project.id)
        assert getattr(project, "description", "") == "Test without avatar config"

    def test__project_avatar_generic_upload_error(self, project):
        """Test generic exception handling during avatar upload"""
        # Use a directory path as avatar - this will cause IsADirectoryError
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              avatar: "/tmp"
        """

        # Should not fail - avatar failure is now handled with warning
        run_gitlabform(config, project)

        # Avatar should remain unchanged (not set due to failure)
        project = project.manager.get(project.id)
        assert project.avatar_url is None or "gravatar" in project.avatar_url

    def test__project_avatar_error_continues_with_next_processor(self, project_for_function, other_project):
        """
        Test that when terminate_after_error=False, GitLabForm continues processing
        other projects even when one project's avatar fails.

        This demonstrates the current architecture's support for project-level
        granularity in error handling.
        """
        from gitlabform import GitLabForm

        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should be set successfully"
        # Reset other_project description to known value because it's class scoped and may have been set by other tests
        other_project.description = None
        other_project.save()
        original_other_description = None

        # Store original descriptions to verify changes
        original_project = project_for_function.manager.get(project_for_function.id)
        original_other_project = other_project.manager.get(other_project.id)
        original_other_description = getattr(original_other_project, "description", "")

        # Determine which project comes first alphabetically
        projects = [project_for_function, other_project]
        projects_sorted = sorted(projects, key=lambda p: p.path_with_namespace)

        first_project = projects_sorted[0]
        second_project = projects_sorted[1]

        # Now build the config so that first_project is the one that should fail and stop processing
        config = f"""
        projects_and_groups:
          {first_project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
          {second_project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
        """

        # Create GitLabForm instance directly (this will use test mode)
        gf = GitLabForm(target="ALL_DEFINED", config_string=config)  # Process all projects defined in config

        # Override the terminate_after_error setting to test non-terminate behavior
        gf.terminate_after_error = False

        # This should now run without terminating immediately
        # The first project should fail due to avatar, but the second project should be processed
        # Note: It will still exit with SystemExit at the end due to _show_summary
        with pytest.raises(SystemExit) as exc_info:
            gf.run()

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh project data and verify the behavior:
        # 1. First project: description should be changed because it's non-avatar config, which is processed first
        # 2. avatar setting failed
        # 3. gitlabform continues processing other projects due to terminate_after_error=False or `--terminate` CLI option is not set
        updated_project = first_project.manager.get(first_project.id)
        current_description = getattr(updated_project, "description", "")
        # assert current_description == original_description
        assert current_description == test_description

        # 2. Second project: description SHOULD be changed because gitlabform continues processing other projects due to terminate_after_error=False or `--terminate` CLI option is not set
        updated_other_project = second_project.manager.get(second_project.id)
        current_other_description = getattr(updated_other_project, "description", "")
        assert current_other_description == test_description
        assert current_other_description != original_other_description

    def test__project_avatar_error_stops_all_processing(self, project_for_function, other_project):
        """
        Test that when terminate_after_error=True (default), GitLabForm stops processing
        immediately when the first project's avatar fails.

        This demonstrates the default terminate behavior at project-level.
        """
        from gitlabform import GitLabForm

        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should NOT be set due to early termination"

        # Reset other_project description to known value because it's class scoped and may have been set by other tests
        other_project.description = None
        other_project.save()

        # Store original descriptions to verify they don't change
        original_project = project_for_function.manager.get(project_for_function.id)
        original_other_project = other_project.manager.get(other_project.id)
        original_other_description = getattr(original_other_project, "description", "")

        # Determine which project comes first alphabetically
        projects = [project_for_function, other_project]
        projects_sorted = sorted(projects, key=lambda p: p.path_with_namespace)

        first_project = projects_sorted[0]
        second_project = projects_sorted[1]

        # Now build the config so that first_project is the one that should fail and stop processing
        config = f"""
        projects_and_groups:
          {first_project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
          {second_project.path_with_namespace}:
            project_settings:
              description: "{test_description}"
        """

        # Create GitLabForm instance directly (this will use test mode)
        gf = GitLabForm(target="ALL_DEFINED", config_string=config)  # Process all projects defined in config

        # Use the default terminate_after_error=True behavior
        # This should terminate immediately when the first project fails

        # Should fail with SystemExit due to immediate termination
        with pytest.raises(SystemExit) as exc_info:
            gf.run()

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh project data and verify the behavior:
        # 1. First project: description should be changed because it's non-avatar config, which is processed first
        # 2. avatar setting failed
        # 3. gitlabform stops processing other projects due to terminate_after_error=True or `--terminate` CLI option is set
        updated_project = first_project.manager.get(first_project.id)
        current_description = getattr(updated_project, "description", "")
        assert current_description == test_description

        # 2. Second project: description should NOT be changed because gitlabform stops processing other projects due to terminate_after_error=True or `--terminate` CLI option is set
        updated_other_project = second_project.manager.get(second_project.id)
        current_other_description = getattr(updated_other_project, "description", "")
        assert current_other_description == original_other_description
        assert current_other_description != test_description
