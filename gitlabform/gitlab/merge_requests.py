from gitlabform.gitlab.core import GitLabCore


class GitLabMergeRequests(GitLabCore):

    def create_mr(self, project_and_group_name, source_branch, target_branch, title, description=None):
        pid = self._get_project_id(project_and_group_name)
        data = {
            "id": pid,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }
        return self._make_requests_to_api("projects/%s/merge_requests", pid, method='POST', data=data,
                                          expected_codes=201)

    def accept_mr(self, project_and_group_name, mr_id):  # NOT iid, like API docs suggest!
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_request/%s/merge", (pid, mr_id), method='PUT')

    def update_mr(self, project_and_group_name, mr_id, data):  # NOT iid, like API docs suggest!
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/merge_request/%s", (pid, mr_id), method='PUT', data=data)

    def get_mrs(self, project_and_group_name):
        """
        :param project_and_group_name: like 'group/project'
        :return: get all *open* MRs in given project
        """
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_requests?scope=all&state=opened", pid, paginated=True)

    def get_mr(self, project_and_group_name, mr_id):  # NOT iid, like API docs suggest!
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_requests/%s", (pid, mr_id))

    def get_mr_approvals(self, project_and_group_name, mr_id):  # NOT iid, like API docs suggest!
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_requests/%s/approvals", (pid, mr_id))
