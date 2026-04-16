import pytest
from gitlab import Gitlab
from gitlab.v4.objects import Project

from tests.acceptance import run_gitlabform
from gitlabform.processors.project.project_security_settings import (
    ProjectSecuritySettingsProcessor,
)

pytestmark = pytest.mark.requires_ultimate_license


class TestProjectSecuritySettings:
    def test__secret_push_protection_project_security_settings(self, gl, project):

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_security_settings:
              secret_push_protection_enabled: true
        """

        run_gitlabform(config, project)

        updated_project_security_settings = self.get_project_security_settings(project, gl)

        assert updated_project_security_settings["secret_push_protection_enabled"] is True

    @staticmethod
    def get_project_security_settings(project: Project, gl: Gitlab):
        path = f"/projects/{project.id}/security_settings"
        return gl.http_get(path)
