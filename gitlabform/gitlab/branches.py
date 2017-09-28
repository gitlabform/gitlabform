from gitlabform.gitlab.core import GitLabCore


class GitLabBranches(GitLabCore):

    def protect_branch(self, project_and_group_name, branch, developers_can_push, developers_can_merge):
        pid = self._get_project_id(project_and_group_name)
        data = {
            "id": pid,
            "branch": branch,
            "developers_can_push": developers_can_push,
            "developers_can_merge": developers_can_merge,
        }
        return self._make_requests_to_api("projects/%s/repository/branches/%s/protect" % (pid, branch),
                                          method='PUT', data=data,
                                          expected_codes=[200, 201])

    def unprotect_branch(self, project_and_group_name, branch):
        pid = self._get_project_id(project_and_group_name)
        data = {
            "id": pid,
            "branch": branch,
        }
        return self._make_requests_to_api("projects/%s/repository/branches/%s/unprotect" % (pid, branch),
                                          method='PUT', data=data,
                                          expected_codes=[200, 201])

    def get_branches(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        result = self._make_requests_to_api("projects/%s/repository/branches" % pid)
        return sorted(map(lambda x: x['name'], result))

    def get_branch(self, project_and_group_name, branch):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/branches/%s" % (pid, branch))
