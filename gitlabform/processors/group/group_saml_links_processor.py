from logging import debug
from typing import List


from gitlabform.gitlab import GitLab
from gitlab.base import RESTObject, RESTObjectList
from gitlab.v4.objects import Group
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSAMLLinksProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("saml_group_links", gitlab)

    def _process_configuration(self, group_path: str, configuration: dict) -> None:
        """Process the SAML links configuration for a group."""

        configured_links = configuration.get("saml_group_links", {})
        enforce_links = configuration.get("saml_group_links|enforce", False)

        group: Group = self.gl.get_group_by_path_cached(group_path)
        existing_links: RESTObjectList | List[RESTObject] = self._fetch_saml_links(
            group
        )
        existing_link_names = [existing_link.name for existing_link in existing_links]

        # Remove 'enforce' key from the config so that it's not treated as a "link"
        if enforce_links:
            configured_links.pop("enforce")

        for link_name, link_configuration in configured_links.items():
            if link_name not in existing_link_names:
                group.saml_group_links.create(link_configuration)
                group.save()

        if enforce_links:
            self._delete_extra_links(group, existing_links, configured_links)

    def _fetch_saml_links(self, group: Group) -> RESTObjectList | List[RESTObject]:
        """Fetch the existing SAML links for a group."""
        return group.saml_group_links.list()

    def _delete_extra_links(
        self,
        group: Group,
        existing: RESTObjectList | List[RESTObject],
        configured: dict,
    ) -> None:
        """Delete any SAML links that are not in the configuration."""
        known_names = [
            common_name["name"]
            for common_name in configured.values()
            if common_name != "enforce"
        ]

        for link in existing:
            if link.name not in known_names:
                debug(f"Deleting extra SAML link: {link.name}")
                group.saml_group_links.delete(link.id)