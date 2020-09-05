from gitlabform.gitlab.core import GitLabCore


class GitLabBranches(GitLabCore):
    def protect_branch(
        self, project_and_group_name, branch, developers_can_push, developers_can_merge
    ):
        data = {
            "id": project_and_group_name,
            "branch": branch,
            "developers_can_push": developers_can_push,
            "developers_can_merge": developers_can_merge,
        }
        return self._make_requests_to_api(
            "projects/%s/repository/branches/%s/protect",
            (project_and_group_name, branch),
            method="PUT",
            data=data,
            expected_codes=[200, 201],
        )

    def branch_access_level(
        self,
        project_and_group_name,
        branch,
        push_access_level,
        merge_access_level,
        unprotect_access_level,
    ):
        return self._make_requests_to_api(
            "projects/%s/protected_branches?name=%s&push_access_level=%s&merge_access_level=%s&unprotect_access_level=%s",
            (
                project_and_group_name,
                branch,
                push_access_level,
                merge_access_level,
                unprotect_access_level,
            ),
            method="POST",
            data={},
            expected_codes=[200, 201, 409],
        )

    def unprotect_branch(self, project_and_group_name, branch):
        data = {
            "id": project_and_group_name,
            "branch": branch,
        }
        return self._make_requests_to_api(
            "projects/%s/repository/branches/%s/unprotect",
            (project_and_group_name, branch),
            method="PUT",
            data=data,
            expected_codes=[200, 201],
        )

    def unprotect_branch_new_api(self, project_and_group_name, branch):
        # 404 means that the branch is already unprotected
        return self._make_requests_to_api(
            "projects/%s/protected_branches/%s",
            (project_and_group_name, branch),
            method="DELETE",
            expected_codes=[200, 201, 204, 404],
        )

    def get_branches(self, project_and_group_name):
        result = self._make_requests_to_api(
            "projects/%s/repository/branches", project_and_group_name, paginated=True
        )
        return sorted(map(lambda x: x["name"], result))

    def get_branch(self, project_and_group_name, branch):
        return self._make_requests_to_api(
            "projects/%s/repository/branches/%s", (project_and_group_name, branch)
        )

    def get_branch_access_levels(self, project_and_group_name, branch):
        return self._make_requests_to_api(
            "projects/%s/protected_branches/%s", (project_and_group_name, branch)
        )

    def create_branch(
        self, project_and_group_name, new_branch_name, create_branch_from_ref
    ):
        data = {
            "id": project_and_group_name,
            "branch": new_branch_name,
            "ref": create_branch_from_ref,
        }
        self._make_requests_to_api(
            "projects/%s/repository/branches",
            (project_and_group_name),
            method="POST",
            data=data,
            expected_codes=[200, 201],
        )

    def delete_branch(self, project_and_group_name, branch):
        self._make_requests_to_api(
            "projects/%s/repository/branches/%s",
            (project_and_group_name, branch),
            method="DELETE",
            expected_codes=[200, 204],
        )

    def get_protected_branches(self, project_and_group_name):
        branches = self._make_requests_to_api(
            "projects/%s/repository/branches", project_and_group_name, paginated=True
        )

        protected_branches = []
        for branch in branches:
            if branch["protected"]:
                name = branch["name"]
                protected_branches.append(name)

        return protected_branches

    def get_unprotected_branches(self, project_and_group_name):
        branches = self._make_requests_to_api(
            "projects/%s/repository/branches", project_and_group_name, paginated=True
        )

        unprotected_branches = []
        for branch in branches:
            if not branch["protected"]:
                name = branch["name"]
                unprotected_branches.append(name)

        return unprotected_branches
