from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class GroupPushRulesProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_push_rules",
            gitlab,
            get_method_name="get_group_push_rules",
            edit_method_name="put_group_push_rules",
            add_method_name="post_group_push_rules",
        )
