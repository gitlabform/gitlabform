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

    def test__add_saml_links_premium(self, gl, project, group):

        assert len(group.saml_group_links.list()) == 0, "saml_group_links is not empty"
        add_group_saml_settings = f"""
        projects_and_groups:
          {group.full_path}/*:              
             saml_group_links: 
               devops_are_maintainers:                                 
                 saml_group_name: devops_maintainer,
                 access_level: maintainer
        """
        run_gitlabform(add_group_saml_settings, group)
        refreshed_group = gl.groups.get(group.id)
        assert len(refreshed_group.saml_group_links.list()) == 1

    def test__enforce_saml_links_premium(self, gl, group_for_function):

        assert (
            len(group_for_function.saml_group_links.list()) == 0
        ), "saml_group_links is not empty"

        add_group_saml_settings = f"""
          projects_and_groups:
            {group_for_function.full_path}/*:              
              saml_group_links: 
                devops_are_maintainers:                                 
                  saml_group_name: devops_maintainer
                  access_level: maintainer
                developers_are_developers:
                  saml_group_name: developers
                  access_level: developer
                analysts_are_reporters:
                  saml_group_name: analysts_reporter
                  access_level: reporter
          """
        run_gitlabform(add_group_saml_settings, group_for_function)
        refreshed_group = gl.groups.get(group_for_function.id)
        assert len(refreshed_group.saml_group_links.list()) == 3

        add_group_saml_settings_enforce = f"""
          projects_and_groups:
            {group_for_function.full_path}/*:              
              saml_group_links: 
                analysts_are_reporters:
                  saml_group_name: analysts_reporter
                  access_level: reporter
                enforce: true
          """
        run_gitlabform(add_group_saml_settings_enforce, group_for_function)
        refreshed_group = gl.groups.get(group_for_function.id)
        saml_group_links = refreshed_group.saml_group_links.list()
        assert len(saml_group_links) == 1
        assert saml_group_links[0].name == "analysts_reporter"
        assert saml_group_links[0].access_level == AccessLevel.get_value("reporter")
