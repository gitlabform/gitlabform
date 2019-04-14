from gitlabform.gitlab.core import GitLabCore


class GitLabMembers(GitLabCore):

    def add_member_to_project(self, project_and_group_name, user, access_level, expires_at):
        data = {
            "user_id": self._get_user_id(user),
            "access_level": access_level,
            "expires_at": expires_at
        }
        return self._make_requests_to_api("projects/%s/members", project_and_group_name, method='POST',
                                         data=data, expected_codes=201)

    def remove_member_from_project(self, project_and_group_name, user):
        return self._make_requests_to_api("projects/%s/members/%s", (project_and_group_name, self._get_user_id(user)),
                                          method='DELETE', expected_codes=204)
