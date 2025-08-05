import pytest

from tests.acceptance import run_gitlabform
from gitlabform.gitlab import AccessLevel

pytestmark = pytest.mark.requires_license


class TestGroupSettings:
    def test__edit_new_setting_premium(self, gl, project, group):
        assert "file_template_project_id" not in group.attributes

        edit_group_settings = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_settings:
              file_template_project_id: {project.id}
        """

        run_gitlabform(edit_group_settings, group)

        refreshed_group = gl.groups.get(group.id)
        assert refreshed_group.file_template_project_id == project.id
