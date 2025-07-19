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

    def test__group_avatar_file_not_found_continues_with_warning(self, group):
        """Test that non-existent avatar file shows warning but continues processing"""
        nonexistent_path = "/path/to/nonexistent/image.png"

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "{nonexistent_path}"
        """

        # Should not fail - avatar failure is now handled with warning
        run_gitlabform(config, group)

        # Avatar should remain unchanged (not set due to failure)
        group = group.manager.get(group.id)
        assert group.avatar_url is None or "gravatar" in group.avatar_url

    def test__group_avatar_no_avatar_config(self, group):
        """Test that no avatar config is handled gracefully"""
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              description: "Test without avatar config"
        """

        # Should work fine without avatar config
        run_gitlabform(config, group)

        # Verify other settings are applied
        group = group.manager.get(group.id)
        assert getattr(group, "description", "") == "Test without avatar config"

    def test__group_avatar_generic_upload_error(self, group):
        """Test generic exception handling during avatar upload"""
        # Use a directory path as avatar - this will cause IsADirectoryError
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              avatar: "/tmp"
        """

        # Should not fail - avatar failure is now handled with warning
        run_gitlabform(config, group)

        # Avatar should remain unchanged (not set due to failure)
        group = group.manager.get(group.id)
        assert group.avatar_url is None or "gravatar" in group.avatar_url

    def test__group_avatar_error_continues_with_next_processor(self, group_for_function, other_group):
        """
        Test that when terminate_after_error=False, GitLabForm continues processing
        other groups even when one group's avatar fails.

        This demonstrates the current architecture's support for group-level
        granularity in error handling.
        """
        from gitlabform import GitLabForm

        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should be set successfully"

        # Reset other_group description to known value because it's class scoped and may have been set by other tests
        other_group.description = None
        other_group.save()

        # Store original descriptions to verify changes
        original_group = group_for_function.manager.get(group_for_function.id)
        original_other_group = other_group.manager.get(other_group.id)

        # Determine which group comes first alphabetically
        groups = [group_for_function, other_group]
        groups_sorted = sorted(groups, key=lambda g: g.full_path)

        first_group = groups_sorted[0]
        second_group = groups_sorted[1]

        # Now build the config so that first_group is the one that should fail and stop processing
        config = f"""
        projects_and_groups:
          {first_group.full_path}/*:
            group_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
          {second_group.full_path}/*:
            group_settings:
              description: "{test_description}"
        """

        # Create GitLabForm instance directly (this will use test mode)
        gf = GitLabForm(target="ALL_DEFINED", config_string=config)  # Process all groups defined in config

        # Override the terminate_after_error setting to test non-terminate behavior
        gf.terminate_after_error = False

        # This should now run without terminating immediately
        # The first group should fail due to avatar, but the second group should be processed
        # Note: It will still exit with SystemExit at the end due to _show_summary
        with pytest.raises(SystemExit) as exc_info:
            gf.run()

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh group data and verify the behavior:
        # 1. First group: description should be changed because it's non-avatar config, which is processed first
        # 2. avatar setting failed
        # 3. gitlabform continues processing other groups due to terminate_after_error=False or `--terminate` CLI option is not set
        updated_group = first_group.manager.get(first_group.id)
        current_description = getattr(updated_group, "description", "")
        assert current_description == test_description

        # 2. Second group: description SHOULD be changed because gitlabform continues processing other groups due to terminate_after_error=False or `--terminate` CLI option is not set
        updated_other_group = second_group.manager.get(second_group.id)
        current_other_description = getattr(updated_other_group, "description", "")
        assert current_other_description == test_description

    def test__group_avatar_error_stops_all_processing(self, group_for_function, other_group):
        """
        Test that when terminate_after_error=True (default), GitLabForm stops processing
        immediately when the first group's avatar fails.

        This demonstrates the default terminate behavior at group-level.
        """
        from gitlabform import GitLabForm

        nonexistent_path = "/path/to/nonexistent/image.png"
        test_description = "Test description that should NOT be set due to early termination"

        # Reset other_group description to known value because it's class scoped and may have been set by other tests
        other_group.description = None
        other_group.save()

        # Store original descriptions to verify they don't change
        original_group = group_for_function.manager.get(group_for_function.id)
        original_other_group = other_group.manager.get(other_group.id)
        original_other_description = getattr(original_other_group, "description", "")

        # Determine which group comes first alphabetically
        groups = [group_for_function, other_group]
        groups_sorted = sorted(groups, key=lambda g: g.full_path)

        first_group = groups_sorted[0]
        second_group = groups_sorted[1]

        # Now build the config so that first_group is the one that should fail and stop processing
        config = f"""
        projects_and_groups:
          {first_group.full_path}/*:
            group_settings:
              description: "{test_description}"
              avatar: "{nonexistent_path}"
          {second_group.full_path}/*:
            group_settings:
              description: "{test_description}"
        """

        # Create GitLabForm instance directly (this will use test mode)
        gf = GitLabForm(target="ALL_DEFINED", config_string=config)  # Process all groups defined in config

        # Use the default terminate_after_error=True behavior
        # This should terminate immediately when the first group fails

        # Should fail with SystemExit due to immediate termination
        with pytest.raises(SystemExit) as exc_info:
            gf.run()

        # Verify it's the expected exit code for processing errors
        assert exc_info.value.code == 2

        # Refresh group data and verify the behavior:
        # 1. First group: description should be changed because it's non-avatar config, which is processed first
        # 2. avatar setting failed
        # 3. gitlabform stops processing other groups due to terminate_after_error=True or `--terminate` CLI option is set
        updated_group = first_group.manager.get(first_group.id)
        current_description = getattr(updated_group, "description", "")
        assert current_description == test_description

        # 2. Second group: description should NOT be changed because gitlabform stops processing other groups due to terminate_after_error=True or `--terminate` CLI option is set
        updated_other_group = second_group.manager.get(second_group.id)
        current_other_description = getattr(updated_other_group, "description", "")
        assert current_other_description == original_other_description
        assert current_other_description != test_description
