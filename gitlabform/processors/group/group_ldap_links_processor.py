import sys
from logging import critical, info
from typing import Dict, List, Optional, Tuple

from gitlab.exceptions import GitlabListError
from gitlab.v4.objects import Group, GroupLDAPGroupLink

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

# A rule is identified by provider + exactly one of (cn, filter).
DefiningKey = Tuple[Optional[str], Optional[str], Optional[str]]


class GroupLDAPLinksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_ldap_links", gitlab)

    def _process_configuration(self, group_path_and_name: str, configuration: Dict):
        configured_links: Dict = configuration.get("group_ldap_links", {})
        enforce = configured_links.pop("enforce", False)

        self._find_duplicates(group_path_and_name, configured_links)

        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)
        existing_links: List[GroupLDAPGroupLink] = self._list_existing_links(group)

        handled_keys: set = set()

        for entity_name, link_config in configured_links.items():
            if not self._has_defining_keys(link_config):
                critical(
                    f"Entity {entity_name} in group_ldap_links for {group_path_and_name}"
                    f" doesn't have its defining keys: 'provider' and ('cn' or 'filter')"
                )
                sys.exit(EXIT_INVALID_INPUT)

            key = self._defining_key_of_config(link_config)
            matching = next(
                (link for link in existing_links if self._defining_key_of_link(link) == key),
                None,
            )

            if link_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of group_ldap_links in {group_path_and_name}")
                    matching.delete()
                handled_keys.add(key)
                continue

            self._validate_required(group_path_and_name, entity_name, link_config)

            if matching:
                if self._needs_update(matching.asdict(), link_config):
                    # The API doesn't support updating an LDAP link, so we delete and recreate.
                    info(f" * Recreating {entity_name} of group_ldap_links in {group_path_and_name}")
                    matching.delete()
                    self._create_link(group, link_config)
                else:
                    info(f" * {entity_name} of group_ldap_links in {group_path_and_name} doesn't need an update.")
            else:
                info(f" * Adding {entity_name} of group_ldap_links in {group_path_and_name}")
                self._create_link(group, link_config)
            handled_keys.add(key)

        if enforce:
            for existing in existing_links:
                key = self._defining_key_of_link(existing)
                if key not in handled_keys:
                    info(
                        f"Deleting LDAP link (provider={existing.provider},"
                        f" cn={getattr(existing, 'cn', None)},"
                        f" filter={getattr(existing, 'filter', None)})"
                        f" in {group_path_and_name} as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    @staticmethod
    def _list_existing_links(group: Group) -> List[GroupLDAPGroupLink]:
        # GitLab returns 404 (not an empty list) when a group has no LDAP links configured;
        # python-gitlab surfaces that as GitlabListError.
        try:
            return list(group.ldap_group_links.list(get_all=True))
        except GitlabListError as e:
            if getattr(e, "response_code", None) == 404:
                return []
            raise

    @staticmethod
    def _create_link(group: Group, link_config: Dict) -> None:
        data = {k: v for k, v in link_config.items() if k != "delete"}
        group.ldap_group_links.create(data)

    @staticmethod
    def _has_defining_keys(link_config: Dict) -> bool:
        return link_config.get("provider") is not None and (
            link_config.get("cn") is not None or link_config.get("filter") is not None
        )

    @staticmethod
    def _defining_key_of_config(link_config: Dict) -> DefiningKey:
        return (link_config.get("provider"), link_config.get("cn"), link_config.get("filter"))

    @staticmethod
    def _defining_key_of_link(link: GroupLDAPGroupLink) -> DefiningKey:
        return (link.provider, getattr(link, "cn", None), getattr(link, "filter", None))

    @classmethod
    def _find_duplicates(cls, group_path_and_name: str, configured_links: Dict) -> None:
        seen: Dict[DefiningKey, str] = {}
        for name, entry in configured_links.items():
            if not cls._has_defining_keys(entry):
                continue
            key = cls._defining_key_of_config(entry)
            if key in seen:
                critical(
                    f"Entities {seen[key]} and {name} in group_ldap_links for {group_path_and_name}"
                    f" are the same in terms of their defining keys: 'provider' and ('cn' or 'filter')"
                )
                sys.exit(EXIT_INVALID_INPUT)
            seen[key] = name

    @staticmethod
    def _validate_required(group_path_and_name: str, entity_name: str, link_config: Dict) -> None:
        missing: List[str] = []
        if link_config.get("provider") is None:
            missing.append("'provider'")
        cn_set = link_config.get("cn") is not None
        filter_set = link_config.get("filter") is not None
        if cn_set == filter_set:
            # neither or both are set — both are invalid (exclusive)
            missing.append("exactly one of ('cn', 'filter')")
        if missing:
            critical(
                f"Entity {entity_name} in group_ldap_links for {group_path_and_name}"
                f" doesn't have some of its keys required to create or update:"
                f" {', '.join(missing)}"
            )
            sys.exit(EXIT_INVALID_INPUT)
