import base64

from gitlabform.gitlab.core import GitLabCore


class GitLabRepositories(GitLabCore):
    def get_commits_with_string_in_compare_results(
        self, project_and_group_name, c_from, c_to, with_string
    ):
        compare_results = self.compare(project_and_group_name, c_from, c_to)
        commits = compare_results["commits"]
        return [commit for commit in commits if with_string in commit["title"]]

    def compare(self, project_and_group_name, c_from, c_to):
        return self._make_requests_to_api(
            "projects/%s/repository/compare?from=%s&to=%s",
            (project_and_group_name, c_from, c_to),
        )

    def get_file(self, project_and_group_name, branch, path):
        result = self._make_requests_to_api(
            "projects/%s/repository/files/%s?ref=%s",
            (project_and_group_name, path, branch),
        )
        return base64.b64decode(result["content"]).decode("utf-8")

    def set_file(self, project_and_group_name, branch, path, content, commit_message):
        data = {
            "branch": branch,
            "file_path": path,
            "content": content,
            "commit_message": commit_message,
        }
        return self._make_requests_to_api(
            "projects/%s/repository/files/%s",
            (project_and_group_name, path),
            "PUT",
            data=data,
        )

    def add_file(self, project_and_group_name, branch, path, content, commit_message):
        data = {
            "branch": branch,
            "file_path": path,
            "content": content,
            "commit_message": commit_message,
        }
        return self._make_requests_to_api(
            "projects/%s/repository/files/%s",
            (project_and_group_name, path),
            "POST",
            data=data,
            expected_codes=201,
        )

    def delete_file(self, project_and_group_name, branch, path, commit_message):
        data = {"branch": branch, "file_path": path, "commit_message": commit_message}
        return self._make_requests_to_api(
            "projects/%s/repository/files/%s",
            (project_and_group_name, path),
            "DELETE",
            data=data,
            expected_codes=[200, 204],
        )
