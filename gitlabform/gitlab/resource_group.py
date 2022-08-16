from gitlabform.gitlab.projects import GitLabProjects


class GitLabResourceGroup(GitLabProjects):
    def get_specific_resource_group(self, project_and_group_name, resource_group_name):
        return self._make_requests_to_api(
            "projects/%s/resource_groups/%s",
            (project_and_group_name, resource_group_name),
            method="GET",
            expected_codes=[200],
        )

    def update_resource_group(
        self, project_and_group_name, resource_group_name, process_mode
    ):
        return self._make_requests_to_api(
            "projects/%s/resource_groups/%s",
            (project_and_group_name, resource_group_name),
            method="PUT",
            expected_codes=[200],
            data=process_mode,
        )
