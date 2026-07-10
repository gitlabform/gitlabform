from logging import debug
from typing import List

from gitlabform.gitlab import GitLab
from gitlab.v4.objects import Group, GroupSAMLGroupLink
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSAMLLinksProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("group_saml_links", gitlab)

    def _process_configuration(self, group_path_and_name: str, configuration: dict) -> None:
        """Process the SAML links configuration for a group."""

        configured_section = configuration.get("group_saml_links", {}) or {}
        enforce_links = configuration.get("group_saml_links|enforce", False)

        configured_links = {k: v for k, v in configured_section.items() if k != "enforce"}

        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)
        existing_links: List[GroupSAMLGroupLink] = group.saml_group_links.list(get_all=True)
        existing_by_name = {link.name: link for link in existing_links}

        for _, link_configuration in configured_links.items():
            saml_group_name = link_configuration.get("saml_group_name")
            existing_link = existing_by_name.get(saml_group_name)

            if existing_link is None:
                group.saml_group_links.create(link_configuration)
                continue

            # GitLab API's request and response attributes differs when SAML link is created vs retrieved.
            # On creation or retrieving a link, attribute is called `saml_group_name` but and returned response is 'name' instead.
            # To compare existing link (retrieved from GitLab) with configured link, link configuration need to replace `saml_group_name` with `name`
            expected = {**link_configuration, "name": saml_group_name}
            expected.pop("saml_group_name", None)

            if self._needs_update(existing_link.asdict(), expected):
                # GitLab API has no update endpoint for SAML links; delete and recreate instead.
                debug(f"Updating SAML link: {saml_group_name} with {link_configuration}")
                existing_link.delete()
                group.saml_group_links.create(link_configuration)

        if enforce_links:
            self._delete_extra_links(group, existing_links, configured_links)

    def _delete_extra_links(
        self,
        group: Group,
        existing: List[GroupSAMLGroupLink],
        configured: dict,
    ) -> None:
        """Delete any SAML links that are not in the configuration."""
        known_names = {link["saml_group_name"] for link in configured.values()}

        for link in existing:
            if link.name not in known_names:
                debug(f"Deleting extra SAML link: {link.name}")
                group.saml_group_links.delete(link.name)
