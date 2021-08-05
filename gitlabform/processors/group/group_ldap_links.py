from gitlabform.gitlab import GitLab
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class GroupLDAPLinksProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_ldap_links",
            gitlab,
            "get_ldap_group_links",
            "add_ldap_group_link",
            "delete_ldap_group_link",
            ["cn", "filter"],
        )
