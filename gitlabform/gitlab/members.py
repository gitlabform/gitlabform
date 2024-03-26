from gitlabform.gitlab.core import GitLabCore


class GitLabMembers(GitLabCore):

    def add_member_to_project(
        self,
        project_and_group_name,
        username,
        access_level,
        expires_at=None,
    ):
        user_id = self._get_user_id(username)
        data = {"user_id": user_id, "access_level": access_level}
        if expires_at:
            data["expires_at"] = expires_at

        return self._make_requests_to_api(
            "projects/%s/members",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def remove_member_from_project(self, project_and_group_name, username):
        user_id = self._get_user_id(username)

        # 404 means that the user is already not a member of the project, so let's accept it for idempotency
        return self._make_requests_to_api(
            "projects/%s/members/%s",
            (project_and_group_name, user_id),
            method="DELETE",
            expected_codes=[204, 404],
        )

    def edit_member_of_project(
        self, group_name, username, access_level, expires_at=None
    ):
        user_id = self._get_user_id(username)
        data = {"user_id": user_id, "access_level": access_level}
        if expires_at:
            data["expires_at"] = expires_at

        return self._make_requests_to_api(
            "projects/%s/members/%s",
            (group_name, user_id),
            method="PUT",
            data=data,
            expected_codes=200,
        )

    def get_members_from_project(self, project_and_group_name):
        # note that this DOES NOT return inherited users
        members = self._make_requests_to_api(
            "projects/%s/members", project_and_group_name
        )
        # it will return {username1: {...api info about username1...}, username2: {...}}
        # otherwise it can get very long to iterate when checking if a user
        # is already in the project if there are a lot of users to check.
        # To enforce case insensitivity, the username is always as lowercase as
        # it can be for future comparisons.
        final_members = {}
        for member in members:
            final_members[member["username"].lower()] = member

        return final_members
