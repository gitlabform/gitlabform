from logging import debug, warning
from typing import List
from cli_ui import info

from gitlabform.gitlab import GitLab
from gitlab.v4.objects import Group, GroupSAMLGroupLink
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSAMLLinksProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("group_saml_links", gitlab)

    def _process_configuration(self, group_path: str, configuration: dict) -> None:
        """Process the SAML links configuration for a group."""

        configured_links = configuration.get("group_saml_links", {})
        enforce_links = configuration.get("group_saml_links|enforce", False)

        group: Group = self.gl.get_group_by_path_cached(group_path)
        existing_links: List[GroupSAMLGroupLink] = group.saml_group_links.list(get_all=True)
        existing_link_names = [existing_link.name for existing_link in existing_links]

        # Remove 'enforce' key from the config so that it's not treated as a "link"
        if enforce_links:
            configured_links.pop("enforce")

        # Process each configured SAML link
        for _, link_configuration in configured_links.items():
            saml_group_name = link_configuration.get("saml_group_name")

            if saml_group_name not in existing_link_names:
                # Create the saml link as it does not already exist
                group.saml_group_links.create(link_configuration)
                group.save()
            else:
                # Check if the existing link needs to be updated
                # GitLab API does not provide an endpoint for updating SAML links
                # If update required, we need to delete and recreate
                existing_link_config = next((link for link in existing_links if link.name == saml_group_name), None)
                if existing_link_config and self._needs_update(existing_link_config.asdict(), link_configuration):
                    debug(f"Updating SAML link: {saml_group_name} with {link_configuration}")
                    existing_link_config.delete()
                    group.saml_group_links.create(link_configuration)
                    group.save()

        # Process enforce mode
        if enforce_links:
            self._delete_extra_links(group, existing_links, configured_links)

    def _delete_extra_links(
        self,
        group: Group,
        existing: List[GroupSAMLGroupLink],
        configured: dict,
    ) -> None:
        """Delete any SAML links that are not in the configuration."""
        known_names = [
            common_name["saml_group_name"] for common_name in configured.values() if common_name != "enforce"
        ]

        for link in existing:
            if link.name not in known_names:
                debug(f"Deleting extra SAML link: {link.name}")
                group.saml_group_links.delete(link.name)
