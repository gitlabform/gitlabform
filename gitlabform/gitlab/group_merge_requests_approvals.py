from gitlabform.gitlab.core import (
    NotFoundException,
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

    # approval rules
    def get_group_approval_rules(self, project_and_group_name):
        gid = self._get_group_id(project_and_group_name)
        return self._make_requests_to_api("groups/%s/approval_rules", gid)

    def get_group_approval_rule(self, project_and_group_name, name):
        gid = self._get_group_id(project_and_group_name)
        rules = self._make_requests_to_api("groups/%s/approval_rules", gid)
        for rule in rules:
            if rule["name"] == name:
                return rule
        raise NotFoundException

    def add_group_approval_rule(
        self,
        project_and_group_name: str,
        data,
    ):
        gid = self._get_group_id(project_and_group_name)

        self._make_requests_to_api(
            "groups/%s/approval_rules",
            gid,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def edit_group_approval_rule(
        self,
        project_and_group_name,
        rule_in_gitlab,
        rule_in_config,
    ):
        gid = self._get_group_id(project_and_group_name)
        approval_rule_id = rule_in_gitlab["id"]

        self._make_requests_to_api(
            "groups/%s/approval_rules/%s",
            (gid, approval_rule_id),
            method="PUT",
            data=None,
            json=rule_in_config,
        )

    def delete_group_approval_rule(self, project_and_group_name, rule_in_gitlab):
        pid = self._get_project_id(project_and_group_name)
        approval_rule_id = rule_in_gitlab["id"]

        self._make_requests_to_api(
            "groups/%s/approval_rules/%s",
            (pid, approval_rule_id),
            method="DELETE",
            expected_codes=[200, 204],
        )
