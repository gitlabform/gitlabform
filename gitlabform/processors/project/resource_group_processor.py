from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class ResourceGroupProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "resource_group",
            gitlab,
            list_method_name="get_specific_resource_group",
            add_method_name="",
            delete_method_name="",
            defining=Key("name"),
            required_to_create_or_update=And(Key("name"), Key("process_mode")),
            edit_method_name="update_resource_group",
        )
