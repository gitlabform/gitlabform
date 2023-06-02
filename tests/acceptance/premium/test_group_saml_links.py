from tests.acceptance import run_gitlabform
from gitlabform.gitlab import Gitlab, Group, AccessLevel


class TestGroupSamlLinks:
    def test__create_group_saml_link(self, gl: Gitlab, group_for_function: Group):
        config_group_saml_link = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_saml_links:
              dev_as_developer: # just a label
                saml_group_name: saml_dev
                access_level: developer
        """

        run_gitlabform(config_group_saml_link, group_for_function)

        refreshed_group = gl.groups.get(group_for_function.id)
        saml_group_links = refreshed_group.saml_group_links.list()
        assert len(saml_group_links) == 1

        saml_group_link = saml_group_links[0]
        assert saml_group_link.name == "saml_dev"
        assert saml_group_link.access_level == AccessLevel.DEVELOPER.value
