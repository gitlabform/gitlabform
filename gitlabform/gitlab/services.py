from gitlabform.gitlab.core import GitLabCore


class GitLabServices(GitLabCore):

    def set_service(self, project_and_group_name, service, data):
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/services/%s", (pid, service), 'PUT', data, expected_codes=[200, 201])

    def delete_service(self, project_and_group_name, service):
        pid = self._get_project_id(project_and_group_name)
        self._make_requests_to_api("projects/%s/services/%s", (pid, service), 'DELETE', expected_codes=[200, 204])
