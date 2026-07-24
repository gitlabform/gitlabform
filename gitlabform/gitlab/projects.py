from gitlabform.gitlab.core import GitLabCore, NotFoundException


class GitLabProjects(GitLabCore):
    def get_project_case_insensitive(self, some_string):
        # maybe "foo/bar" is some project's path

        try:
            # try with exact case
            return self.get_project(some_string)
        except NotFoundException:
            # try case insensitive
            projects = self._make_requests_to_api(
                f"projects?search=%s&simple=true",
                some_string.lower(),
                method="GET",
            )
            for project in projects:
                if project["path_with_namespace"].lower() == some_string.lower():
                    return project
            raise NotFoundException(f"Project with path '{some_string}' not found.")

    def get_groups_from_project(self, project_and_group_name):
        # couldn't find an API call that was giving me directly
        # the shared groups, so I'm using directly the GET /projects/:id call
        project_info = self._make_requests_to_api("projects/%s", project_and_group_name)

        # it will return {group_name: {...api info about group_name...}, ...}
        groups = {}
        for group in project_info["shared_with_groups"]:
            groups[group["group_full_path"]] = group

        return groups

    def share_with_group(self, project_and_group_name, group_name, group_access, expires_at):
        data = {"group_id": self._get_group_id(group_name), "expires_at": expires_at}
        if group_access is not None:
            data["group_access"] = group_access
        return self._make_requests_to_api(
            "projects/%s/share",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def unshare_with_group(self, project_and_group_name, group_name):
        # 404 means that the group already has not access, so let's accept it for idempotency
        group_id = self._get_group_id(group_name)
        return self._make_requests_to_api(
            "projects/%s/share/%s",
            (project_and_group_name, group_id),
            method="DELETE",
            expected_codes=[204, 404],
        )
