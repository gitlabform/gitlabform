from time import sleep

from gitlabform.gitlab.core import (
    GitLabCore,
    NotFoundException,
    TimeoutWaitingForDeletion,
)


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

    def create_project(
        self,
        name,
        path,
        namespace_id,
        default_branch=None,
        wait_if_still_being_deleted=False,
    ):
        data = {
            "name": name,
            "path": path,
            "namespace_id": namespace_id,
        }
        if default_branch:
            data["default_branch"] = default_branch

        if wait_if_still_being_deleted:
            # GitLab deletes the project asynchronously, it may take a few seconds.
            # So if you are creating new project with the same name as the one
            # that is still being deleted, GitLab returns code 400
            # and "The project is still being deleted.". Let's retry a few times
            # then to start creating when the deletion is done.
            # (Note: this code DOES NOT support the "Delayed Project deletion" feature
            # where the actual deletion can be postponed for days!)

            max_retries = 10
            wait_before_retry = 3
            retry = 0

            while True:
                retry += 1

                if retry > max_retries:
                    raise TimeoutWaitingForDeletion

                response = self._make_requests_to_api("projects", data=data, method="POST", expected_codes=[201, 400])
                if self._is_project_still_deleted(response):
                    # wait & retry
                    sleep(wait_before_retry)
                    continue
                else:
                    return response

        else:
            return self._make_requests_to_api("projects", data=data, method="POST", expected_codes=201)

    @staticmethod
    def _is_project_still_deleted(response):
        # check if response looks like this:
        # {'message': {'base': ['The project is still being deleted. Please try again later.'],
        # 'limit_reached': []}}
        return (
            "message" in response
            and "base" in response["message"]
            and type(response["message"]["base"]) == list
            and len(response["message"]["base"]) == 1
            and "The project is still being deleted." in response["message"]["base"][0]
        )

    def delete_project(self, project_and_group_name):
        # 404 means that the project does not exist anymore, so let's accept it for idempotency
        return self._make_requests_to_api(
            "projects/%s",
            project_and_group_name,
            method="DELETE",
            expected_codes=[202, 204, 404],
        )

        # GitLab deletes the project asynchronously, it may take a few seconds
        # BUT it doesn't return such not yet deleted project in GET calls, so
        # there is no point in checking if it actually done here. :(
        # See create_project() for the code that deals with that.

    def get_all_projects(self, include_archived=False):
        """
        :param include_archived: if the archived projects should be returned too
        :return: sorted list of ALL projects you have access to, strings like: "group/project_name"
        """
        try:
            # there are 3 states of the "archived" flag: true, false, undefined
            # we use the last 2
            if include_archived:
                query_string = "order_by=name&sort=asc"
            else:
                query_string = "order_by=name&sort=asc&archived=false"
            result = self._make_requests_to_api(f"projects?{query_string}")
            return sorted(map(lambda x: x["path_with_namespace"], result))
        except NotFoundException:
            return []


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
