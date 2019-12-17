from gitlabform.gitlab.core import GitLabCore, UnexpectedResponseException


class GitLabMembers(GitLabCore):

    def add_member_to_project(self, project_and_group_name, user, access_level, expires_at):
        data = {
            "user_id": self._get_user_id(user),
            "expires_at": expires_at
        }
        if access_level is not None:
            data['access_level'] = access_level
        return self._make_requests_to_api("projects/%s/members", project_and_group_name, method='POST',
                                         data=data, expected_codes=201)

    def remove_member_from_project(self, project_and_group_name, user):
        return self._make_requests_to_api("projects/%s/members/%s", (project_and_group_name, self._get_user_id(user)),
                                          method='DELETE', expected_codes=204)

    def add_member_to_group(self, group_name, user, access_level, expires_at):
        data = {
            "user_id": self._get_user_id(user),
            "expires_at": expires_at
        }
        if access_level is not None:
            data['access_level'] = access_level
        return self._make_requests_to_api("groups/%s/members", group_name, method='POST',
                                         data=data, expected_codes=201)

    def update_member_of_group(self, group_name, user, access_level, expires_at):
        user_id =self._get_user_id(user)
        data = {
            "user_id": user_id,
            "expires_at": expires_at
        }
        if access_level is not None:
            data['access_level'] = access_level
        return self._make_requests_to_api("groups/%s/members/%s", (group_name, user_id), method="PUT",
                                         data=data, expected_codes=200)


    def remove_member_from_group(self, group_name, user):
        self._make_requests_to_api("groups/%s/members/%s", (group_name, self._get_user_id(user)),
                                        method='DELETE', expected_codes=204)

