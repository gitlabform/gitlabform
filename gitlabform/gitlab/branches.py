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
        return self._make_requests_to_api("projects/%s/repository/branches/%s/protect", (pid, branch),
                                          method='PUT', data=data,
                                          expected_codes=[200, 201])

    def unprotect_branch(self, project_and_group_name, branch):
        pid = self._get_project_id(project_and_group_name)
        data = {
            "id": pid,
            "branch": branch,
        }
        return self._make_requests_to_api("projects/%s/repository/branches/%s/unprotect", (pid, branch),
                                          method='PUT', data=data,
                                          expected_codes=[200, 201])

    def get_branches(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)
        result = self._make_requests_to_api("projects/%s/repository/branches", pid)
        return sorted(map(lambda x: x['name'], result))

    def get_branch(self, project_and_group_name, branch):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/branches/%s", (pid, branch))

    def delete_branch(self, group_and_project_name, branch):
        pid = self._get_project_id(group_and_project_name)
        self._make_requests_to_api("projects/%s/repository/branches/%s", (pid, branch), method='DELETE')

    def get_protected_branches(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)

        branches = self._make_requests_to_api("projects/%s/repository/branches", pid)

        protected_branches = []
        for branch in branches:
            if branch['protected']:
                name = branch['name']
                protected_branches.append(name)

        return protected_branches

    def get_unprotected_branches(self, project_and_group_name):
        pid = self._get_project_id(project_and_group_name)

        branches = self._make_requests_to_api("projects/%s/repository/branches", pid)

        feature_branches = []
        for branch in branches:
            if not branch['protected']:
                name = branch['name']
                feature_branches.append(name)

        return feature_branches
