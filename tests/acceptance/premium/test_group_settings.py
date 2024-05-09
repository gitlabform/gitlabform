import pytest

from tests.acceptance import run_gitlabform

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

    def test__add_saml_links_premium(self, gl, project, group):

        # assert len(group.saml_group_links.list()) == 0, "saml_group_links is not empty"

        add_group_settings = f"""
        projects_and_groups:
          {group.full_path}/*:
              group_saml_links: 
                devops_are_maintainers: 
                  saml_group_name: devops,
                  access_level": 50
        """

        run_gitlabform(add_group_settings, group)

        refreshed_group = gl.groups.get(group.id)
        assert len(refreshed_group.saml_group_links.list()) == 1
