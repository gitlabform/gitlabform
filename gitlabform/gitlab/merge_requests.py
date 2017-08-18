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
        return self._make_requests_to_api("projects/%s/merge_requests" % pid, method='POST', data=data,
                                          expected_codes=201)

    def accept_mr(self, project_and_group_name, mr_id):  # NOT iid, like API docs suggest!
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_request/%s/merge" % (pid, mr_id), method='PUT')

    def get_mrs(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/merge_requests" % pid, paginated=True)
