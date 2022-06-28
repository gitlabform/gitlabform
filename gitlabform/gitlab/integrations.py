from gitlabform.gitlab.core import GitLabCore


class GitLabIntegrations(GitLabCore):
    def get_integration(self, project_and_group_name, integration):
        return self._make_requests_to_api(
            "projects/%s/integrations/%s", (project_and_group_name, integration)
        )

    def set_integration(self, project_and_group_name, integration, data):
        # DO NOT CHANGE BELOW json=data, it is necessary to pass data as JSON
        # for the Integrations API to work FULLY properly!
        # see https://gitlab.com/gitlab-org/gitlab/-/issues/202216 for more info.
        self._make_requests_to_api(
            "projects/%s/integrations/%s",
            (project_and_group_name, integration),
            "PUT",
            data=None,
            expected_codes=[200, 201],
            json=data,
        )

    def delete_integration(self, project_and_group_name, integration):
        self._make_requests_to_api(
            "projects/%s/integrations/%s",
            (project_and_group_name, integration),
            "DELETE",
            expected_codes=[200, 204],
        )
