from tests.acceptance import run_gitlabform


class TestProjectSettings:
    def test__builds_for_private_projects(self, gitlab, group_and_project):
        settings = gitlab.get_project_settings(group_and_project)
        assert settings["visibility"] == "private"

        config_builds_for_private_projects = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              visibility: internal
        """

        run_gitlabform(config_builds_for_private_projects, group_and_project)

        settings = gitlab.get_project_settings(group_and_project)
        assert settings["visibility"] == "internal"
