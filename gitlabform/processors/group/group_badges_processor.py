from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class GroupBadgesProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_badges",
            gitlab,
            list_method_name="get_group_badges",
            add_method_name="add_group_badge",
            delete_method_name="delete_group_badge",
            defining=Key("name"),
            required_to_create_or_update=And(
                Key("name"), Key("link_url"), Key("image_url")
            ),
            edit_method_name="edit_group_badge",
        )
