from cli_ui import fatal

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

    def _can_proceed(self, project_or_group: str, configuration: dict):
        if "approvals_before_merge" in configuration["merge_requests_approvals"]:
            fatal(
                "Setting the 'approvals_before_merge' in the 'merge_requests_approvals' sections is not allowed "
                "as it is not clear which rule does it apply to. "
                "Please set it inside the specific approval rules in the 'merge_requests_approval_rules' section."
            )
        else:
            return True
