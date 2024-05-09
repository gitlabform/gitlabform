from logging import debug
from typing import List

from gitlabform.gitlab import GitLab
from gitlab.v4.objects import Group
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSAMLLinksProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("group_saml_links", gitlab)

    def _process_configuration(self, group_path: str, configuration: dict) -> None:
        """Process the SAML links configuration for a group."""

        configured_links = configuration.get("group_saml_links", {})
        enforce_links = configuration.get("group_saml_links|enforce", False)

        group: Group = self.gl.get_group_by_path_cached(group_path)
        existing_links: List[dict] = self._fetch_saml_links(group)

        # Remove 'enforce' key from the config so that it's not treated as a "link"
        if enforce_links:
            configured_links.pop("enforce")

        for link_name, link_configuration in configured_links.items():
            if link_name not in [
                existing_link["saml_group_name"] for existing_link in existing_links
            ]:
                group.saml_group_links.create(link_configuration)

        if enforce_links:
            self._delete_extra_links(group, existing_links, configured_links)

    def _fetch_saml_links(self, group: Group) -> List[dict]:
        """Fetch the existing SAML links for a group."""
        links = group.saml_group_links.list()
        return [link.attributes for link in links]

    def _delete_extra_links(
        self, group: Group, existing: List[dict], configured: dict
    ) -> None:
        """Delete any SAML links that are not in the configuration."""
        known_names = [
            common_name["saml_group_name"]
            for common_name in configured.values()
            if common_name != "enforce"
        ]

        for link in existing:
            if link["saml_group_name"] not in known_names:
                debug(f"Deleting extra SAML link: {link['saml_group_name']}")
                group.saml_group_links.delete(link["id"])
