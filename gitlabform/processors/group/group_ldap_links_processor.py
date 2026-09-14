from logging import info
from typing import Dict, List, Optional, Tuple

from gitlab.exceptions import GitlabListError
from gitlab.v4.objects import Group, GroupLDAPGroupLink

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

# A link is identified by provider + exactly one of (cn, filter).
DefiningKey = Tuple[Optional[str], Optional[str], Optional[str]]


class GroupLDAPLinksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_ldap_links", gitlab)

    def _process_configuration(self, group_path_and_name: str, configuration: Dict):
        configured_links: Dict = configuration.get("group_ldap_links", {})
        enforce = configured_links.pop("enforce", False)

        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)
        existing_links: List[GroupLDAPGroupLink] = self._list_existing_links(group)

        processed_keys: set = set()

        for entity_name, link_config in configured_links.items():
            key = self._defining_key_of_config(link_config)
            matching = next(
                (link for link in existing_links if self._defining_key_of_link(link) == key),
                None,
            )

            if link_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of {self.configuration_name} in {group_path_and_name}")
                    matching.delete()
                else:
                    info(
                        f"Not deleting {entity_name} of {self.configuration_name} in {group_path_and_name},"
                        f" because it doesn't exist"
                    )
                processed_keys.add(key)
                continue

            if matching:
                if self._needs_update(matching.asdict(), link_config):
                    # The API has no endpoint to update an LDAP link
                    # (https://docs.gitlab.com/api/group_ldap_links/), so we recreate it.
                    info(f" * Recreating {entity_name} of {self.configuration_name} in {group_path_and_name}")
                    matching.delete()
                    self._create_link(group, link_config)
                else:
                    info(
                        f" * {entity_name} of {self.configuration_name} in {group_path_and_name}"
                        f" doesn't need an update."
                    )
            else:
                info(f" * Adding {entity_name} of {self.configuration_name} in {group_path_and_name}")
                self._create_link(group, link_config)
            processed_keys.add(key)

        if enforce:
            for existing in existing_links:
                if self._defining_key_of_link(existing) not in processed_keys:
                    info(
                        f"Deleting LDAP link (provider={existing.provider},"
                        f" cn={getattr(existing, 'cn', None)},"
                        f" filter={getattr(existing, 'filter', None)})"
                        f" of {self.configuration_name} in {group_path_and_name}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    @staticmethod
    def _list_existing_links(group: Group) -> List[GroupLDAPGroupLink]:
        # GitLab returns 404 (not an empty list) when a group has no LDAP links configured;
        # python-gitlab surfaces that as GitlabListError.
        try:
            return group.ldap_group_links.list(get_all=True)
        except GitlabListError as e:
            if e.response_code == 404:
                return []
            raise

    @staticmethod
    def _create_link(group: Group, link_config: Dict) -> None:
        # GitLab returns 404 instead of 400 when the create parameters are invalid
        # (e.g. a non-existent provider), so a 404 here does not mean a missing group.
        group.ldap_group_links.create(link_config)

    @staticmethod
    def _defining_key_of_config(link_config: Dict) -> DefiningKey:
        return (link_config.get("provider"), link_config.get("cn"), link_config.get("filter"))

    @staticmethod
    def _defining_key_of_link(link: GroupLDAPGroupLink) -> DefiningKey:
        return (link.provider, getattr(link, "cn", None), getattr(link, "filter", None))
