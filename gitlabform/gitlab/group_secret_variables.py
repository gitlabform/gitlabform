from gitlabform.gitlab.core import GitLabCore


class GitLabGroupSecretVariables(GitLabCore):
    def get_group_secret_variables(self, group):
        return self._make_requests_to_api("groups/%s/variables", group)

    def post_group_secret_variable(self, group, secret_variable):
        # secret_variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable
        self._make_requests_to_api(
            "groups/%s/variables", group, "POST", secret_variable, expected_codes=201
        )

    def delete_group_secret_variable(self, group, secret_variable_object):
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, secret_variable_object["key"]),
            "DELETE",
            expected_codes=[204, 404],
        )

    def put_group_secret_variable(
        self, group, secret_variable_in_gitlab, secret_variable_in_config
    ):
        # secret_variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, secret_variable_in_gitlab["key"]),
            "PUT",
            secret_variable_in_config,
        )

    def get_group_secret_variable(self, group, secret_variable_key):
        return self._make_requests_to_api(
            "groups/%s/variables/%s", (group, secret_variable_key)
        )["value"]

    def get_group_secret_variable_object(self, group, secret_variable_key):
        return self._make_requests_to_api(
            "groups/%s/variables/%s", (group, secret_variable_key)
        )
