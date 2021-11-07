from gitlabform.gitlab.core import GitLabCore


class GitLabMembers(GitLabCore):
    def get_project_members(self, project_and_group_name, all=False):
        url_template = "projects/%s/members"
        if all:
            url_template += "/all"

        return self._make_requests_to_api(
            url_template, project_and_group_name, paginated=True
        )

    def get_shared_with_groups(self, project_and_group_name):
        # a dict with groups that this project has been shared with
        return self._make_requests_to_api("projects/%s", project_and_group_name)[
            "shared_with_groups"
        ]

    def add_member_to_project(
        self, project_and_group_name, username, access_level, expires_at=None
    ):
        data = {"user_id": self._get_user_id(username), "expires_at": expires_at}
        if access_level is not None:
            data["access_level"] = access_level

        return self._make_requests_to_api(
            "projects/%s/members",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def remove_member_from_project(self, project_and_group_name, user):
        # 404 means that the user is already not a member of the project, so let's accept it for idempotency
        return self._make_requests_to_api(
            "projects/%s/members/%s",
            (project_and_group_name, self._get_user_id(user)),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def get_group_members(self, group_name, all=False):
        url_template = "groups/%s/members"
        if all:
            url_template += "/all"

        return self._make_requests_to_api(url_template, group_name, paginated=True)

    def get_members_from_project(self, project_and_group_name):
        members = self._make_requests_to_api(
            "projects/%s/members", project_and_group_name, paginated=True
        )
        # it will return {username1: {...api info about username1...}, username2: {...}}
        # otherwise it can get very long to iterate when checking if a user
        # is already in the project if there are a lot of users to check
        final_members = {}
        for member in members:
            final_members[member["username"]] = member

        return final_members

    def add_member_to_group(self, group_name, username, access_level, expires_at=None):
        data = {"user_id": self._get_user_id(username), "expires_at": expires_at}
        if access_level is not None:
            data["access_level"] = access_level

        return self._make_requests_to_api(
            "groups/%s/members",
            group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def remove_member_from_group(self, group_name, user):
        # 404 means that the user is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s/members/%s",
            (group_name, self._get_user_id(user)),
            method="DELETE",
            expected_codes=[204, 404],
        )
