from gitlabform.gitlab.core import GitLabCore


class GitLabCommits(GitLabCore):

    def get_commit(self, project_and_group_name, sha):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/commits/%s", (pid, sha))
