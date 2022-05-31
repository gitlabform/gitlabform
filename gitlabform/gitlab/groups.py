import functools

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
            raise NotFoundException(
                f"Group/subgroup with path '{some_string}' not found."
            )

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
        result = self._make_requests_to_api("groups?all_available=true")
        return sorted(map(lambda x: x["full_path"], result))

    def get_projects(self, group, include_archived=False, only_names=True):
        """
        :param group: group name
        :param include_archived: set to True if archived projects should also be returned
        :param only_names: set to False to get the whole project objects
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
                f"groups/%s/projects?{query_string}", group
            )
        except NotFoundException:
            projects = []

        project_and_groups_in_group_namespace = [
            project
            for project in projects
            if project["path_with_namespace"].startswith(group + "/")
        ]

        if only_names:
            return sorted(
                map(
                    lambda x: x["path_with_namespace"],
                    project_and_groups_in_group_namespace,
                )
            )
        else:
            return sorted(
                project_and_groups_in_group_namespace,
                key=lambda x: x["path_with_namespace"],
            )

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

    def get_group_shared_with(self, group):
        group = self.get_group_case_insensitive(group)

        return group["shared_with_groups"]

    def add_share_to_group(
        self, group, share_with_group_name, group_access, expires_at=None
    ):
        share_with_group_id = self.get_group_id_case_insensitive(share_with_group_name)
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
        share_with_group_id = self.get_group_id_case_insensitive(share_with_group_name)

        # 404 means that the user is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s/share/%s",
            (group, share_with_group_id),
            method="DELETE",
            expected_codes=[204, 404],
        )
