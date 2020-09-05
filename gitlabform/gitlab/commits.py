from gitlabform.gitlab.core import GitLabCore


class GitLabCommits(GitLabCore):
    def get_commit(self, project_and_group_name, sha):
        return self._make_requests_to_api(
            "projects/%s/repository/commits/%s", (project_and_group_name, sha)
        )

    def get_ahead_and_behind(
        self, project_and_group_name, protected_branch, feature_branch
    ):
        ahead = 0
        behind = 0

        response = self._make_requests_to_api(
            "projects/%s/repository/compare?from=%s&to=%s",
            (project_and_group_name, protected_branch, feature_branch),
        )
        if len(response) > 0:
            ahead = len(response["commits"])

        response = self._make_requests_to_api(
            "projects/%s/repository/compare?from=%s&to=%s",
            (project_and_group_name, feature_branch, protected_branch),
        )
        if len(response) > 0:
            behind = len(response["commits"])

        return ahead, behind

    def get_last_commit_attributes(self, project_and_group_name, branch):
        branch = self._make_requests_to_api(
            "projects/%s/repository/branches/%s", (project_and_group_name, branch)
        )

        last_commit_hash = branch["commit"]["id"]

        commit = self._make_requests_to_api(
            "projects/%s/repository/commits/%s",
            (project_and_group_name, last_commit_hash),
        )

        # we want to read git's *commit date* instead of *author date*, so that "touching" the branch will invalidate
        # its "getting older" counter

        return commit["author_name"], commit["author_email"], commit["committed_date"]
