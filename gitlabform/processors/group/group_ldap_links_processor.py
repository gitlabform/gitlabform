from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import And, Or, Key, Xor
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class GroupLDAPLinksProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_ldap_links",
            gitlab,
            list_method_name="get_ldap_group_links",
            add_method_name="add_ldap_group_link",
            delete_method_name="delete_ldap_group_link",
            defining=And(Key("provider"), Or(Key("cn"), Key("filter"))),
            required_to_create_or_update=And(
                Key("provider"), Xor(Key("cn"), Key("filter"))
            ),
        )
