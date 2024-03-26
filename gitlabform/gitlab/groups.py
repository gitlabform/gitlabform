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

    def get_group(self, name):
        return self._make_requests_to_api("groups/%s", name)

    def get_groups(self):
        """
        :return: sorted list of groups
        """

        if self.admin:
            query = "all_available=true"
        else:
            # as a non-admin it's pointless to get groups with a lower role than Reporter
            # - it's the minimal role that is needed to manage something (f.e. group labels)
            query = f"min_access_level=20"

        result = self._make_requests_to_api(f"groups?{query}")

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
                query1 = "include_subgroups=true"
            else:
                query1 = "include_subgroups=true&archived=false"

            if self.admin:
                query2 = "all_available=true"
            else:
                # it's pointless to get projects with a lower role than Reporter
                # - it's the minimal role that is needed to manage something (f.e. labels)
                query2 = f"min_access_level=20"

            projects = self._make_requests_to_api(
                f"groups/%s/projects?{query1}&{query2}", group
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
