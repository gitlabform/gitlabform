from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class MergeRequestsApprovals(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "merge_requests_approvals",
            gitlab,
            get_method_name="get_approvals_settings",
            edit_method_name="post_approvals_settings",
        )
