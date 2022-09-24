from gitlabform.gitlab.projects import GitLabProjects


class GitLabVariables(GitLabProjects):
    def get_variables(self, project_and_group_name):
        return self._make_requests_to_api(
            "projects/%s/variables", project_and_group_name
        )

    def post_variable(self, project_and_group_name, variable_in_config):
        # variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable
        self._make_requests_to_api(
            "projects/%s/variables",
            project_and_group_name,
            "POST",
            variable_in_config,
            expected_codes=201,
        )

    def put_variable(
        self,
        project_and_group_name,
        variable_in_gitlab,
        variable_in_config,
    ):
        # variable has to be like documented at:
        # https://docs.gitlab.com/ce/api/build_variables.html#update-variable
        self._make_requests_to_api(
            "projects/%s/variables/%s",
            (project_and_group_name, variable_in_gitlab["key"]),
            "PUT",
            variable_in_config,
        )

    def delete_variable(self, project_and_group_name, variable_in_config):
        self._make_requests_to_api(
            "projects/%s/variables/%s",
            (project_and_group_name, variable_in_config["key"]),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def get_variable(self, project_and_group_name, variable_key, environment_scope="*"):
        if environment_scope == "*":
            url = "projects/%s/variables/%s"
        else:
            url = f"projects/%s/variables/%s?filter[environment_scope]={environment_scope}"
        return self._make_requests_to_api(url, (project_and_group_name, variable_key))[
            "value"
        ]
