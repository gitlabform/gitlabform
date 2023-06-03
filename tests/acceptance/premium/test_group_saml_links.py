from tests.acceptance import run_gitlabform
from gitlab import Gitlab
from gitlabform.gitlab import AccessLevel


class TestGroupSamlLinks:
    def test__create_group_saml_link(self, gl: Gitlab, group_for_function):
        config_group_saml_link = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_saml_links:
              dev_as_developer: # just a label
                saml_group_name: saml_dev
                access_level: developer
        """

        saml_group_links = self._update_saml_group_links(
            gl, group_for_function, config_group_saml_link
        )

        assert len(saml_group_links) == 1

        saml_group_link = saml_group_links[0]
        assert saml_group_link.name == "saml_dev"
        assert saml_group_link.access_level == AccessLevel.DEVELOPER.value

    def test__enforce(self, gl: Gitlab, group_for_function):
        initial_config_group_saml_link = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_saml_links:
              dev_as_developer: # just a label
                saml_group_name: saml_dev
                access_level: developer
        """

        initial_saml_group_links = self._update_saml_group_links(
            gl, group_for_function, initial_config_group_saml_link
        )
        assert len(initial_saml_group_links) == 1

        updated_config_group_saml_link = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_saml_links:
              leaddev_as_maintainer: # just a label
                saml_group_name: saml_leaddev
                access_level: maintainer
              enforce: true
        """
        updated_saml_group_links = self._update_saml_group_links(
            gl, group_for_function, updated_config_group_saml_link
        )
        assert len(updated_saml_group_links) == 1

        saml_group_link = updated_saml_group_links[0]
        assert saml_group_link.name == "saml_leaddev"
        assert saml_group_link.access_level == AccessLevel.MAINTAINER.value

    def _update_saml_group_links(
        self, gl: Gitlab, group_for_function, config_group_saml_link
    ):
        run_gitlabform(config_group_saml_link, group_for_function)
        refreshed_group = gl.groups.get(group_for_function.id)
        return refreshed_group.saml_group_links.list()
