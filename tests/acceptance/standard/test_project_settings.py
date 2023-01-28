from tests.acceptance import run_gitlabform


class TestProjectSettings:
    def test__builds_for_private_projects(self, gl, project):
        assert project.visibility == "private"

        config_builds_for_private_projects = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              visibility: internal
        """

        run_gitlabform(config_builds_for_private_projects, project)

        project = gl.projects.get(project.id)
        assert project.visibility == "internal"
