from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class BadgesProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "badges",
            gitlab,
            list_method_name="get_project_badges",
            add_method_name="add_project_badge",
            delete_method_name="delete_project_badge",
            defining=Key("name"),
            required_to_create_or_update=And(Key("name"), Key("link_url"), Key("image_url")),
            edit_method_name="edit_project_badge",
        )
