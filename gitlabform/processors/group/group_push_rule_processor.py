from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class GroupPushRuleProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_push_rule",
            gitlab,
            get_method_name="get_group_push_rule", 
            edit_method_name="edit_group_push_rule",
            add_method_name="add_group_push_rule",
        )

