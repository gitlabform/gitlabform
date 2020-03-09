from gitlabform.gitlab.core import GitLabCore


class GitLabServices(GitLabCore):

    def get_service(self, project_and_group_name, service):
        return self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service))

    def set_service(self, project_and_group_name, service, data):
        # DO NOT CHANGE BELOW json=data , it is necessary to pass data as JSON for Services API to work FULLY properly!
        # see https://gitlab.com/gitlab-org/gitlab/-/issues/202216 for more info.
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'PUT', data=None, expected_codes=[200, 201], json=data)

    def delete_service(self, project_and_group_name, service):
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'DELETE', expected_codes=[200, 204])
