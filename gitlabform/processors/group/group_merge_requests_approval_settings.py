from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class GroupMergeRequestsApprovalSettings(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_merge_requests_approval_settings",
            gitlab,
            get_method_name="get_group_approvals_settings",
            edit_method_name="put_group_approvals_settings",
        )
