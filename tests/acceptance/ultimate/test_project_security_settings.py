from tests.acceptance import run_gitlabform
from gitlabform.processors.project.project_security_settings import (
    ProjectSecuritySettingsProcessor,
)


class TestProjectSecuritySettings:
    def test__secret_push_protection_project_security_settings(self, gl, project):

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_security_settings:
              pre_receive_secret_detection_enabled: true
        """

        run_gitlabform(config, project)

        processor = ProjectSecuritySettingsProcessor(gitlab=gl)
        updated_project_security_settings = processor.get_project_security_settings(project.path_with_namespace)

        assert updated_project_security_settings["pre_receive_secret_detection_enabled"] is True
