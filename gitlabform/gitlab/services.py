from gitlabform.gitlab.core import GitLabCore


class GitLabServices(GitLabCore):

    # TODO: according to docs you actually need project id here...

    def set_service(self, project_and_group_name, service, data):
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'PUT', data, expected_codes=[200, 201])

    def delete_service(self, project_and_group_name, service):
        self._make_requests_to_api("projects/%s/services/%s", (project_and_group_name, service),
                                   'DELETE', expected_codes=[200, 204])
