from gitlabform.gitlab.core import GitLabCore


class GitLabServices(GitLabCore):

    def get_service(self, project_and_group_name, service):
        return self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service))

    def set_service(self, project_and_group_name, service, data):
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'PUT', data=None, expected_codes=[200, 201], json=data)

    def delete_service(self, project_and_group_name, service):
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'DELETE', expected_codes=[200, 204])
