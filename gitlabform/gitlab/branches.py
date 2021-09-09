from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabBranches(GitLabCore):

    # old API
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

    # new API
    def branch_access_level(self, project_and_group_name, branch, protect_settings):

        url = "projects/%s/protected_branches?name=%s"
        parameters_list = [
            project_and_group_name,
            branch,
        ]
        return self._make_requests_to_api(
            url,
            tuple(parameters_list),
            method="POST",
            expected_codes=[
                200,
                201,
                409,
            ],  # TODO: check why is 409 Conflict accepted here :/
            json=protect_settings,
        )

    def branch_code_owner_approval_required(
        self,
        project_and_group_name,
        branch,
        code_owner_approval_required,
    ):
        data = {
            "id": project_and_group_name,
            "branch": branch,
            "code_owner_approval_required": code_owner_approval_required,
        }
        return self._make_requests_to_api(
            "projects/%s/protected_branches/%s",
            (
                project_and_group_name,
                branch,
            ),
            method="PATCH",
            data=data,
            expected_codes=[200, 201],
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

    def get_user_to_protect_branch(self, user_name):
        return self._get_user_id(user_name)

    def get_only_branch_access_levels(self, project_and_group_name, branch):
        try:
            result = self._make_requests_to_api(
                "projects/%s/protected_branches/%s", (project_and_group_name, branch)
            )

            push_access_levels = []
            merge_access_levels = []
            push_access_user_ids = []
            merge_access_user_ids = []
            unprotect_access_level = None

            if "push_access_levels" in result:
                for push_access in result["push_access_levels"]:
                    if not push_access["user_id"]:
                        push_access_levels.append(push_access['access_level'])
                    else:
                        push_access_user_ids.append(push_access['user_id'])

            if "merge_access_levels" in result:
                for merge_access in result["merge_access_levels"]:
                    if not merge_access["user_id"]:
                        merge_access_levels.append(merge_access['access_level'])
                    else:
                        merge_access_user_ids.append(merge_access['user_id'])

            if (
                    "unprotect_access_levels" in result
                    and len(result["unprotect_access_levels"]) == 1
            ):
                unprotect_access_level = result["unprotect_access_levels"][0][
                    "access_level"
                ]
            push_access_levels.sort()
            push_access_user_ids.sort()
            merge_access_user_ids.sort()
            merge_access_user_ids.sort()

            return push_access_levels, merge_access_levels, push_access_user_ids, \
                merge_access_user_ids, unprotect_access_level
        except NotFoundException:
            return None, None, None, None, None

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
            project_and_group_name,
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
