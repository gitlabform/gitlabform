from tests.acceptance import run_gitlabform
from gitlabform.gitlab.project_security_settings import GitlabProjectSecuritySettings


class TestProjectSecuritySettings:
    def test__secret_push_protection_project_security_settings(self, gl, project):

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_security_settings:
              pre_receive_secret_detection_enabled: true
        """

        run_gitlabform(config, project)

        updated_project_security_settings = GitlabProjectSecuritySettings(
            config_string=config
        ).get_project_security_settings(project.path_with_namespace)

        assert updated_project_security_settings["pre_receive_secret_detection_enabled"] is True
