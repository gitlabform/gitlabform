from gitlabform.gitlab.core import GitLabCore


def to_string(x):
    if type(x) is bool:
        # python bool is uppercase and we need a lowercase here
        return "true" if x else "false"
    else:
        return x


class GitLabGroupVariables(GitLabCore):
    def get_group_variables(self, group):
        return self._make_requests_to_api("groups/%s/variables", group)

    def post_group_variable(self, group, variable):
        # variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable

        # workaround for the GitLab bug
        variable = {k: to_string(v) for k, v in variable.items()}

        self._make_requests_to_api("groups/%s/variables", group, "POST", variable, expected_codes=201)

    def delete_group_variable(self, group, variable_object):
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, variable_object["key"]),
            "DELETE",
            expected_codes=[204, 404],
        )

    def put_group_variable(self, group, variable_in_gitlab, variable_in_config):
        # variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable

        # workaround for the GitLab bug
        variable_in_config = {k: to_string(v) for k, v in variable_in_config.items()}

        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, variable_in_gitlab["key"]),
            "PUT",
            variable_in_config,
        )

    def get_group_variable(self, group, variable_key):
        return self._make_requests_to_api("groups/%s/variables/%s", (group, variable_key))["value"]

    def get_group_variable_object(self, group, variable_key):
        return self._make_requests_to_api("groups/%s/variables/%s", (group, variable_key))
