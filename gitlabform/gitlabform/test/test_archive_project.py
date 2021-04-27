from gitlabform.gitlabform.test import (
    run_gitlabform,
)


class TestArchiveProject:
    def test__archive_project(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        config = f"""
        project_settings:
          {group_and_project}:
            project:
              archive: true
        """

        run_gitlabform(config, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

    def test__unarchive_project(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        archive_project = f"""
        project_settings:
          {group_and_project}:
            project:
              archive: true
        """

        unarchive_project = f"""
        project_settings:
          {group_and_project}:
            project:
              archive: false
        """

        run_gitlabform(archive_project, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is True

        run_gitlabform(unarchive_project, group_and_project)
        project = gitlab.get_project(group_and_project)
        assert project["archived"] is False

    def test__dont_edit_archived_project(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        archive_project = f"""
        project_settings:
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
        project_settings:
          {group_and_project}:
            project:
              archive: true

        group_settings:
          {group_and_project}:
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
