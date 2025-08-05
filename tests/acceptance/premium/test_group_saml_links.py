import pytest

from tests.acceptance import run_gitlabform
from gitlabform.gitlab import AccessLevel

pytestmark = pytest.mark.requires_license


class TestGroupSamlLinks:
    def test__add_saml_links(self, gl, group):

        assert len(group.saml_group_links.list()) == 0, "saml_group_links is not empty"
        add_group_saml_settings = f"""
        projects_and_groups:
          {group.full_path}/*:              
             saml_group_links: 
               devops_users:                                 
                 saml_group_name: devops_users
                 access_level: maintainer
        """
        run_gitlabform(add_group_saml_settings, group)

        # Verify that the SAML link was created
        refreshed_group = gl.groups.get(group.id)
        saml_links = refreshed_group.saml_group_links.list(get_all = True)
        assert len(saml_links) == 1
        assert saml_links[0].name == "devops_users"
        assert saml_links[0].access_level == AccessLevel.get_value("maintainer")

    def test__update_saml_links(self, gl, group):

        assert len(group.saml_group_links.list()) == 1, "saml_group_links is not empty from previous test"
        add_group_saml_settings = f"""
        projects_and_groups:
          {group.full_path}/*:              
             saml_group_links: 
               devops_users:                                 
                 saml_group_name: devops_users
                 access_level: developer
        """
        run_gitlabform(add_group_saml_settings, group)
        # Verify that the SAML link was updated
        refreshed_group = gl.groups.get(group.id)
        saml_links = refreshed_group.saml_group_links.list(get_all = True)
        assert len(saml_links) == 1
        assert saml_links[0].name == "devops_users"
        assert saml_links[0].access_level == AccessLevel.get_value("developer")

    def test__enforce_saml_links(self, gl, group_for_function):

        assert len(group_for_function.saml_group_links.list()) == 0, "saml_group_links is not empty"

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
