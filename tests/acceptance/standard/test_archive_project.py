from tests.acceptance import (
    run_gitlabform,
)


class TestArchiveProject:
    def test__archive_project(self, gitlab, group_and_project):

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project:
              archive: true
        """

        run_gitlabform(config, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

    def test__unarchive_project(
        self, gitlab, group_and_project, other_group, other_project
    ):

        archive_project = f"""
        projects_and_groups:
          {group_and_project}:
            project:
              archive: true
        """

        run_gitlabform(archive_project, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

        unarchive_project = f"""
        projects_and_groups:
          {group_and_project}:
            project:
              archive: false
        """

        # 1. if you run gitlabform ALL, but without '--include-archived-projects',
        # then nothing will happen here as the archived project will be omitted when in
        # the effective list of groups and projects

        run_gitlabform(unarchive_project, "ALL", False)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

        # 2. only after you run gitlabform ALL, with '--include-archived-projects'
        # (OR pointing to it that project)
        # the target project will be unarchived
        run_gitlabform(unarchive_project, "ALL")
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is False

    def test__dont_edit_archived_project(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        archive_project = f"""
        projects_and_groups:
          {group_and_project}:
            project:
              archive: true
        """

        run_gitlabform(archive_project, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

        edit_archived_project = f"""
        # the project has to be configured as archived
        # for other configs for it to be ignored
        projects_and_groups:
          {group_and_project}:
            project:
              archive: true

          {group}/*:
            files:
              README.md:
                overwrite: true
                branches:
                  - main
                content: |
                  Some other content that the default one
        """

        run_gitlabform(edit_archived_project, group_and_project)

        # the fact that we are not getting an exception because of trying to edit
        # an archived project means that the test is passing
