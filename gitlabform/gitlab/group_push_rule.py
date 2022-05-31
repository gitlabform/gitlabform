from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupPushRule(GitLabGroups):
    def get_group_push_rule(self, group_path):
        # (unlike the one for project push_rules) this endpoint returns ONLY group push_rules
        return self._make_requests_to_api(
            "groups/%s/push_rule",
            group_path,
        )

    def add_group_push_rule(
        self,
        group_path,
        push_rule_in_config,
    ):
        return self._make_requests_to_api(
            "groups/%s/push_rule",
            group_path,
            method="POST",
            data=push_rule_in_config
        )

    def put_group_push_rule(self, project_and_group_name, push_rule):
        self._make_requests_to_api(
            "groups/%s/push_rule", project_and_group_name, "PUT", push_rule
        )

    def post_group_push_rule(self, project_and_group_name, push_rule):
        self._make_requests_to_api(
            "groups/%s/push_rule", project_and_group_name, "POST", push_rule
        )
