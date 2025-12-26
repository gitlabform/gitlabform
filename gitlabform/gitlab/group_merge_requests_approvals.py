from gitlabform.gitlab.core import (
    GitLabCore,
)


class GitLabGroupMergeRequestsApprovals(GitLabCore):
    # configuration
    # Endpoints only available in Gitlab >=17.7.0
    # https://docs.gitlab.com/17.7/ee/api/merge_request_approval_settings.html#update-group-mr-approval-settings
    def get_group_approvals_settings(self, project_and_group_name):
        gid = self._get_group_id(project_and_group_name)
        return self._make_requests_to_api(
            "groups/%s/merge_request_approval_setting", gid
        )

    def put_group_approvals_settings(
        self, project_and_group_name, group_approval_settings
    ):
        gid = self._get_group_id(project_and_group_name)
        self._make_requests_to_api(
            "groups/%s/merge_request_approval_setting",
            gid,
            "PUT",
            data=group_approval_settings,
            expected_codes=200,
        )
