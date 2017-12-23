import base64

from gitlabform.gitlab.core import GitLabCore


class GitLabRepositories(GitLabCore):

    def get_commits_with_string_in_compare_results(self, project_and_group_name, c_from, c_to, with_string):
        compare_results = self.compare(project_and_group_name, c_from, c_to)
        commits = compare_results['commits']
        return [commit for commit in commits if with_string in commit['title']]

    def compare(self, project_and_group_name, c_from, c_to):
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/compare?from=%s&to=%s", (pid, c_from, c_to))

    def get_file(self, project_and_group_name, branch, path):
        pid = self._get_project_id(project_and_group_name)
        result = self._make_requests_to_api("projects/%s/repository/files?ref=%s&file_path=%s", (pid, branch, path))
        return base64.b64decode(result['content']).decode("utf-8")

    def set_file(self, project_and_group_name, branch, path, content, commit_message):
        data = {
            "branch_name": branch,
            "path": path,
            "content": content,
            "commit_message": commit_message
        }
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/files?ref=%s&file_path=%s", (pid, branch, path),
                                          'PUT', data=data)

    def add_file(self, project_and_group_name, branch, path, content, commit_message):
        data = {
            "branch_name": branch,
            "path": path,
            "content": content,
            "commit_message": commit_message
        }
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/files?ref=%s&file_path=%s", (pid, branch, path),
                                          'POST', data=data, expected_codes=201)

    def delete_file(self, project_and_group_name, branch, path, commit_message):
        data = {
            "branch_name": branch,
            "path": path,
            "commit_message": commit_message
        }
        pid = self._get_project_id(project_and_group_name)
        return self._make_requests_to_api("projects/%s/repository/files?ref=%s&file_path=%s", (pid, branch, path),
                                          'DELETE', data=data)
