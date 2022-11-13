from gitlabform.gitlab.core import (
    NotFoundException,
    GitLabCore,
)


class GitLabProjectMergeRequestsApprovals(GitLabCore):

    # https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-configuration
    def get_approvals_settings(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approvals", pid)

    # https://docs.gitlab.com/ee/api/merge_request_approvals.html#change-configuration
    def post_approvals_settings(self, project_and_group_name, data):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data_required = {"id": pid}
        data = {**data, **data_required}
        self._make_requests_to_api(
            "projects/%s/approvals", pid, "POST", data, expected_codes=201
        )

    def get_approval_rules(self, project_and_group_name):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approval_rules", pid)

    # new syntax
    def delete_approval_rule(self, project_and_group_name, rule_in_gitlab):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        approval_rule_id = rule_in_gitlab["id"]

        self._make_requests_to_api(
            "projects/%s/approval_rules/%s",
            (pid, approval_rule_id),
            method="DELETE",
            expected_codes=[200, 204],
        )

    # TODO: delete
    def delete_approval_rule_by_id(self, project_and_group_name, approval_rule_id):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api(
            "projects/%s/approval_rules/%s",
            (pid, approval_rule_id),
            method="DELETE",
            expected_codes=[200, 204],
        )

    # new syntax
    def add_approval_rule(
        self,
        project_and_group_name,
        data,
    ):
        pid = self._get_project_id(project_and_group_name)

        if "protected_branches" in data:
            self._transform_protected_branches(data, project_and_group_name)

        self._make_requests_to_api(
            "projects/%s/approval_rules",
            pid,
            method="POST",
            data=None,
            expected_codes=201,
            json=data,
        )

    # TODO: delete when not used anymore
    def create_approval_rule(
        self,
        project_and_group_name,
        name,
        approvals_required,
        approvers,
        approver_groups,
    ):
        pid = self._get_project_id(project_and_group_name)

        data = self._create_approval_rule_data(
            project_and_group_name, name, approvals_required, approvers, approver_groups
        )

        self._make_requests_to_api(
            "projects/%s/approval_rules",
            pid,
            method="POST",
            data=None,
            expected_codes=201,
            json=data,
        )

    def get_approval_rule(self, project_and_group_name, name):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        rules = self._make_requests_to_api("projects/%s/approval_rules", pid)
        for rule in rules:
            if rule["name"] == name:
                return rule
        raise NotFoundException

    # new syntax
    def edit_approval_rule(
        self,
        project_and_group_name,
        rule_in_gitlab,
        rule_in_config,
    ):
        pid = self._get_project_id(project_and_group_name)
        approval_rule_id = rule_in_gitlab["id"]

        # not passing any of these lists means: "do not change them"
        # while what we really what is in this case is "clear them"
        if "user_ids" not in rule_in_config:
            rule_in_config["user_ids"] = []
        if "group_ids" not in rule_in_config:
            rule_in_config["group_ids"] = []
        if "protected_branches" in rule_in_config:
            self._transform_protected_branches(rule_in_config, project_and_group_name)
        else:
            rule_in_config["protected_branch_ids"] = []

        self._make_requests_to_api(
            "projects/%s/approval_rules/%s",
            (pid, approval_rule_id),
            method="PUT",
            data=None,
            json=rule_in_config,
        )

    # TODO: delete when not used anymore
    def update_approval_rule(
        self,
        project_and_group_name,
        approval_rule_id,
        name,
        approvals_required,
        approvers,
        approver_groups,
    ):
        pid = self._get_project_id(project_and_group_name)

        data = self._create_approval_rule_data(
            project_and_group_name, name, approvals_required, approvers, approver_groups
        )
        data["approval_rule_id"] = approval_rule_id

        self._make_requests_to_api(
            "projects/%s/approval_rules/%s",
            (pid, approval_rule_id),
            method="PUT",
            data=None,
            json=data,
        )

    def _create_approval_rule_data(
        self,
        project_and_group_name,
        name,
        approvals_required,
        approvers,
        approver_groups,
    ):
        pid = self._get_project_id(project_and_group_name)

        # gitlab API expects ids, not names of users and groups, so we need to convert first
        user_ids = []
        for approver_name in approvers:
            user_ids.append(self._get_user_id(approver_name))
        group_ids = []
        for group_path in approver_groups:
            group_ids.append(int(self._get_group_id(group_path)))

        data = {
            "id": int(pid),
            "name": name,
            "approvals_required": approvals_required,
            "user_ids": user_ids,
            "group_ids": group_ids,
        }

        return data

    def _transform_protected_branches(self, data, project_and_group_name):
        # we do this transformation here instead of in a ConfigurationTransformers
        # because we need a context of the project and group to convert branch names to ids
        # and that is not available there

        protected_branches_name = data["protected_branches"]
        data.pop("protected_branches")
        protected_branch_ids = []
        for branch_name in protected_branches_name:
            branch_id = self._get_protected_branch_id(
                project_and_group_name, branch_name
            )
            protected_branch_ids.append(branch_id)
        data["protected_branch_ids"] = protected_branch_ids
