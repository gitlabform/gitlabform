from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupPushRules(GitLabGroups):
    def get_group_push_rules(self, project_and_group_name: str):
        gid: int = self._get_group_id(project_and_group_name)
        return self._make_requests_to_api(
            "groups/%s/push_rule", gid, "GET", None, [404, 200], None
        )

    def put_group_push_rules(self, project_and_group_name: str, push_rules):
        gid: int = self._get_group_id(project_and_group_name)
        self._make_requests_to_api("groups/%s/push_rule", gid, "PUT", push_rules)

    def post_group_push_rules(self, project_and_group_name: str, push_rules):
        gid: int = self._get_group_id(project_and_group_name)
        self._make_requests_to_api(
            "groups/%s/push_rule", gid, "POST", push_rules, [201], None
        )
