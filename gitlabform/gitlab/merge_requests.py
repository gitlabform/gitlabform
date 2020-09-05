from gitlabform.gitlab.core import GitLabCore


class GitLabMergeRequests(GitLabCore):
    def create_mr(
        self,
        project_and_group_name,
        source_branch,
        target_branch,
        title,
        description=None,
    ):
        data = {
            "id": project_and_group_name,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }
        return self._make_requests_to_api(
            "projects/%s/merge_requests",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def accept_mr(self, project_and_group_name, mr_iid):
        return self._make_requests_to_api(
            "projects/%s/merge_requests/%s/merge",
            (project_and_group_name, mr_iid),
            method="PUT",
        )

    def update_mr(self, project_and_group_name, mr_iid, data):
        self._make_requests_to_api(
            "projects/%s/merge_requests/%s",
            (project_and_group_name, mr_iid),
            method="PUT",
            data=data,
        )

    def get_mrs(self, project_and_group_name):
        """
        :param project_and_group_name: like 'group/project'
        :return: get all *open* MRs in given project
        """
        return self._make_requests_to_api(
            "projects/%s/merge_requests?scope=all&state=opened",
            project_and_group_name,
            paginated=True,
        )

    def get_mr(self, project_and_group_name, mr_iid):
        return self._make_requests_to_api(
            "projects/%s/merge_requests/%s", (project_and_group_name, mr_iid)
        )

    def get_mr_approvals(self, project_and_group_name, mr_iid):
        return self._make_requests_to_api(
            "projects/%s/merge_requests/%s/approvals", (project_and_group_name, mr_iid)
        )
