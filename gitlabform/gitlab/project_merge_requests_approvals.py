from gitlabform.gitlab.core import (
    NotFoundException,
    GitLabCore,
)


class GitLabProjectMergeRequestsApprovals(GitLabCore):
    # configuration

    def get_approvals_settings(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approvals", pid)

    def post_approvals_settings(self, project_and_group_name, data):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        data_required = {"id": pid}
        data = {**data, **data_required}
        self._make_requests_to_api(
            "projects/%s/approvals", pid, "POST", data, expected_codes=201
        )

    # approval rules

    def get_approval_rules(self, project_and_group_name):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/approval_rules", pid)

    def get_approval_rule(self, project_and_group_name, name):
        # for this endpoint GitLab still actually wants pid, not "group/project"...
        pid = self._get_project_id(project_and_group_name)
        rules = self._make_requests_to_api("projects/%s/approval_rules", pid)
        for rule in rules:
            if rule["name"] == name:
                return rule
        raise NotFoundException

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

    def edit_approval_rule(
        self,
        project_and_group_name,
        rule_in_gitlab,
        rule_in_config,
    ):
        pid = self._get_project_id(project_and_group_name)
        approval_rule_id = rule_in_gitlab["id"]

        # GitLab interprets not passing any of these lists as "do not change them"
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
