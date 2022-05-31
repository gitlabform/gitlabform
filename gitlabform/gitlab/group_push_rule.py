from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupPushRule(GitLabGroups):
    def get_group_push_rule(self, group_path):
        return self._make_requests_to_api(
            "groups/%s/push_rule",
            group_path,
        )

    def edit_group_push_rule(self, project_and_group_name, push_rule):
        self._make_requests_to_api(
            "groups/%s/push_rule", project_and_group_name, "PUT", push_rule
        )

    def add_group_push_rule(self, project_and_group_name, push_rule):
        self._make_requests_to_api(
            "groups/%s/push_rule", project_and_group_name, "POST", push_rule
        )

