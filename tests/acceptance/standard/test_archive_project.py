import pytest
from tests.acceptance import (
    get_random_name,
    run_gitlabform,
)


class TestArchiveProject:
    def test__archive_project(self, gl, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project:
              archive: true
        """

        run_gitlabform(config, project.path_with_namespace)

        # Refetch project to get updated info
        project = gl.projects.get(project.id)
        assert project.archived is True

    def test__unarchive_project(self, gl, project):
        # Refresh project to ensure it's unarchived at the start
        project = gl.projects.get(project.id)
        assert project.archived is True

        unarchive_project_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project:
              archive: false
        """

        # 1. if you run gitlabform ALL, but without '--include-archived-projects',
        # then nothing will happen here as the archived project will be omitted when in
        # the effective list of groups and projects

        run_gitlabform(unarchive_project_config, "ALL", False)

        # Refetch project to check if it's still archived
        project = gl.projects.get(project.id)
        assert project.archived is True

        # 2. only after you run gitlabform ALL, with '--include-archived-projects'
        # (OR pointing to it that project)
        # the target project will be unarchived
        run_gitlabform(unarchive_project_config, "ALL")
        project = gl.projects.get(project.id)
        assert project.archived is False

    def test__dont_edit_archived_project(self, gl, project_for_function, capsys):
        """
        Test that editing files in an archived project is not allowed.
        To setup the test, we first need to create a regular unprotected branch
        and then archive the project. After that, we will try to edit a file
        in that archived project on that branch, which should fail.
        """
        # Start with archiving the project for testing
        project = gl.projects.get(project_for_function.id)
        branch_name = get_random_name("feature-branch-")
        project.branches.create({"branch": branch_name, "ref": "main"})
        project.archive()
        assert project.archived is True

        # Prepare a config that would edit the project (change README.md of a feature branch)
        edit_archived_project_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              README.md:
                overwrite: true
                branches:
                  - {branch_name}
                content: |
                  Some test content
        """

        # GitLab now responds with 403 Forbidden when trying to push to an archived project.
        # Since in above config we are trying to push update to an archived project, we expect
        # gitlabform to exit with SystemExit exception.
        with pytest.raises(SystemExit):
            run_gitlabform(edit_archived_project_config, project.path_with_namespace)

        captured = capsys.readouterr()
        assert "403 Forbidden - You are not allowed to push into this branch" in captured.err
