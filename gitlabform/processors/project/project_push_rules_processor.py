from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class ProjectPushRulesProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "project_push_rules",
            gitlab,
            get_method_name="get_project_push_rules",
            edit_method_name="put_project_push_rules",
            add_method_name="post_project_push_rules",
        )
