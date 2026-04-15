from tests.acceptance import (
    run_gitlabform,
)


class TestScheduledForDeletionProject:
    def test__exclude_project_scheduled_for_deletion(self, gl, project_for_function):
        """
        Test that projects scheduled for deletion are excluded by default
        when running gitlabform with ALL target.
        """
        project = gl.projects.get(project_for_function.id)

        # Delete the project - with delayed deletion enabled, this marks it for deletion
        # rather than removing it immediately
        project.delete()

        # Verify the project is now marked for deletion
        project = gl.projects.get(project.id)
        assert project.marked_for_deletion_on is not None

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              description: "modified by gitlabform"
        """

        # 1. Without '--include-projects-scheduled-for-deletion',
        # the project should be omitted from processing
        run_gitlabform(config, "ALL", include_projects_scheduled_for_deletion=False)

        project = gl.projects.get(project.id)
        assert project.description != "modified by gitlabform"

        # 2. With '--include-projects-scheduled-for-deletion',
        # the project should be processed
        run_gitlabform(config, "ALL", include_projects_scheduled_for_deletion=True)

        project = gl.projects.get(project.id)
        assert project.description == "modified by gitlabform"

        # Restore the project so teardown can clean it up
        gl.http_post(f"/projects/{project.id}/restore")
