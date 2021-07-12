import functools
import sys

import cli_ui

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabGroups(GitLabCore):
    @functools.lru_cache()
    def get_group_id_case_insensitive(self, some_string):
        # Cache the mapping from some_string -> id, as that won't change during our run.
        return self.get_group_case_insensitive(some_string)["id"]

    def get_group_case_insensitive(self, some_string):

        # maybe "foo/bar" is some group's path

        try:
            # try with exact case
            return self.get_group(some_string)
        except NotFoundException:

            # try case insensitive
            groups = self._make_requests_to_api(
                "groups?search=%s",
                some_string.lower(),
                method="GET",
            )

            for group in groups:
                if group["full_path"].lower() == some_string.lower():
                    return group
            raise NotFoundException

    def create_group(self, name, path, parent_id=None, visibility="private"):
        data = {
            "name": name,
            "path": path,
            "visibility": visibility,
        }
        if parent_id is not None:
            data["parent_id"] = parent_id
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

    def get_projects(self, group, include_archived=False):
        """
        :param group: group name
        :param include_archived: set to True if archived projects should also be returned
        :return: sorted list of strings "group/project_name". Note that only projects from "group" namespace are
                 returned, so if "group" (= members of this group) is also a member of some projects, they won't be
                 returned here.
        """
        try:
            # there are 3 states of the "archived" flag: true, false, undefined
            # we use the last 2
            if include_archived:
                query_string = "include_subgroups=true"
            else:
                query_string = "include_subgroups=true&archived=false"

            projects = self._make_requests_to_api(
                f"groups/%s/projects?{query_string}", group, paginated=True
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

    def get_group_shared_with(self, group):
        group = self.get_group_case_insensitive(group)

        return group["shared_with_groups"]

    def add_share_to_group(
        self, group, share_with_group_name, group_access, expires_at=None
    ):
        try:
            share_with_group_id = self.get_group_id_case_insensitive(
                share_with_group_name
            )
        except NotFoundException:
            cli_ui.error(f"Group {share_with_group_name} not found.")
            sys.exit(EXIT_INVALID_INPUT)

        data = {"group_id": share_with_group_id, "expires_at": expires_at}
        if group_access is not None:
            data["group_access"] = group_access

        return self._make_requests_to_api(
            "groups/%s/share",
            group,
            method="POST",
            data=data,
            expected_codes=[200, 201],
        )

    def remove_share_from_group(self, group, share_with_group_name):
        try:
            share_with_group_id = self.get_group_id_case_insensitive(
                share_with_group_name
            )
        except NotFoundException:
            cli_ui.error(f"Group {share_with_group_name} not found.")
            sys.exit(EXIT_INVALID_INPUT)

        # 404 means that the user is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s/share/%s",
            (group, share_with_group_id),
            method="DELETE",
            expected_codes=[204, 404],
        )
