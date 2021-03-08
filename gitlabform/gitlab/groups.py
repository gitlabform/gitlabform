from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabGroups(GitLabCore):
    def create_group(self, name, path, visibility="private"):
        data = {
            "name": name,
            "path": path,
            "visibility": visibility,
        }
        return self._make_requests_to_api(
            "groups", data=data, method="POST", expected_codes=201
        )

    def delete_group(self, group_name):
        # 404 means that the group does not exist anymore, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s",
            group_name,
            method="DELETE",
            expected_codes=[200, 202, 204, 404],
        )

    def get_group(self, name):
        return self._make_requests_to_api("groups/%s", name)

    def get_groups(self):
        """
        :return: sorted list of groups
        """
        result = self._make_requests_to_api("groups?all_available=true", paginated=True)
        return sorted(map(lambda x: x["full_path"], result))

    def get_projects(self, group):
        """
        :param group: group name
        :return: sorted list of strings "group/project_name". Note that only projects from "group" namespace are
                 returned, so if "group" (= members of this group) is also a member of some projects, they won't be
                 returned here.
        """
        try:
            projects = self._make_requests_to_api(
                "groups/%s/projects?include_subgroups=true", group, paginated=True
            )
        except NotFoundException:
            projects = []

        all_project_and_groups = sorted(
            map(lambda x: x["path_with_namespace"], projects)
        )

        project_and_groups_in_group_namespace = [
            x for x in all_project_and_groups if x.startswith(group + "/")
        ]

        return project_and_groups_in_group_namespace

    def get_group_settings(self, project_and_group_name):
        try:
            return self._make_requests_to_api("groups/%s", project_and_group_name)
        except NotFoundException:
            return dict()

    def put_group_settings(self, project_and_group_name, group_settings):
        # group_settings has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ee/api/groups.html#update-group
        self._make_requests_to_api(
            "groups/%s", project_and_group_name, "PUT", group_settings
        )

    def delete_group_secret_variable(self, group, secret_variable_key):
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, secret_variable_key),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def post_group_secret_variable(self, group, secret_variable):
        # secret_variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable
        self._make_requests_to_api(
            "groups/%s/variables", group, "POST", secret_variable, expected_codes=201
        )

    def put_group_secret_variable(self, group, secret_variable):
        # secret_variable has to be like documented at:
        # https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, secret_variable["key"]),
            "PUT",
            secret_variable,
        )

    def get_group_secret_variable(self, group, secret_variable_key):
        return self._make_requests_to_api(
            "groups/%s/variables/%s", (group, secret_variable_key)
        )["value"]

    def get_group_secret_variable_object(self, group, secret_variable_key):
        return self._make_requests_to_api(
            "groups/%s/variables/%s", (group, secret_variable_key)
        )

    def get_group_secret_variables(self, group):
        return self._make_requests_to_api("groups/%s/variables", group)

    def delete_group_secret_variable(self, group, secret_variable):
        self._make_requests_to_api(
            "groups/%s/variables/%s",
            (group, secret_variable),
            "DELETE",
            expected_codes=[200, 202, 204, 404],
        )
