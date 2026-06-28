from tests.acceptance import (
    create_group,
    create_project,
    get_random_name,
    run_gitlabform,
)


class TestWildcardPatterns:
    def test__wildcard_project_pattern_all_defined(self, gl):
        """
        Test that a wildcard pattern matches a project when gitlabform runs with
        the ALL_DEFINED target.
        """
        bar_group_name = get_random_name("bar_group")
        bar_group = create_group(bar_group_name)

        bar_project = create_project(bar_group, "bar-project")

        config = f"""
        projects_and_groups:
            '*':
                project_settings:
                    request_access_enabled: true
            {bar_group_name}/bar-*:
                project_settings:
                    request_access_enabled: false
        """

        run_gitlabform(config, "ALL_DEFINED")

        updated = gl.projects.get(bar_project.id)
        assert updated.request_access_enabled is False

    def test__wildcard_project_pattern_with_group_target(self, gl):
        """
        Test that a more specific wildcard pattern overrides a less specific one
        when gitlabform targets a specific group.
        """
        bar_group_name = get_random_name("bar_group")
        bar_group = create_group(bar_group_name)

        bar_project = create_project(bar_group, "bar-project")
        other_project = create_project(bar_group, "other-project")

        config = f"""
        projects_and_groups:
            '*':
                project_settings:
                    request_access_enabled: true
            {bar_group_name}/*:
                project_settings:
                    request_access_enabled: true
            {bar_group_name}/bar-*:
                project_settings:
                    request_access_enabled: false
        """

        run_gitlabform(config, bar_group)

        updated_bar_project = gl.projects.get(bar_project.id)
        updated_other_project = gl.projects.get(other_project.id)

        # Projects matching the wildcard pattern should pick up the override
        assert updated_bar_project.request_access_enabled is False

        # Non-matching project keeps the group-level setting
        assert updated_other_project.request_access_enabled is True
