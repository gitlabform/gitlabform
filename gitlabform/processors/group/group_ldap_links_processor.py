from logging import debug
from typing import List

from gitlabform.gitlab import GitLab
from gitlab.v4.objects import Group
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupLDAPLinksProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("group_ldap_links", gitlab)

    def _process_configuration(self, group_path: str, configuration: dict):

        group: Group = self.gl.get_group_by_path_cached(group_path)

        configured_links = configuration["group_ldap_links"]
        enforce_links = configuration.get("group_ldap_links|enforce", False)

        existing_links: List[dict] = self._fetch_ldap_links(group)

        for name, link_config in configured_links.items():
            if name == "enforce":
                continue

            self._update_ldap_link(group, existing_links, link_config)

        if enforce_links:
            self._delete_extra_links(group, existing_links, configured_links)

    def _fetch_ldap_links(self, group: Group) -> List[dict]:
        links = group.ldapgrouplinks.list(all=True)
        return [link.attributes for link in links]

    def _update_ldap_link(self, group: Group, existing: List[dict], new: dict):
        link_id = self._get_link_id(existing, new)

        if link_id:
            debug(f"Updating LDAP link: {new['cn']}")
            group.ldapgrouplinks.update(link_id, new)
        else:
            debug(f"Creating new LDAP link: {new['cn']}")
            group.ldapgrouplinks.create(new)

    def _get_link_id(self, existing: List[dict], new: dict) -> int | None:
        for link in existing:
            if link["cn"] == new["cn"]:
                return link["id"]

        return None

    def _delete_extra_links(self, group: Group, existing: List[dict], configured: dict):
        known_cns = [c["cn"] for c in configured.values() if c != "enforce"]

        for link in existing:
            if link["cn"] not in known_cns:
                debug(f"Deleting extra LDAP link: {link['cn']}")
                group.ldapgrouplinks.delete(link["id"])
