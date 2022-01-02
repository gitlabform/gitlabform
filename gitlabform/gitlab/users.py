from gitlabform.gitlab.core import GitLabCore


class GitLabUsers(GitLabCore):
    def create_user(self, email, name, username, password):
        data = {
            "email": email,
            "name": name,
            "username": username,
            "password": password,
        }
        return self._make_requests_to_api(
            "users", method="POST", data=data, expected_codes=201
        )

    def get_user_by_name(self, username, user_id=None):
        if not user_id:
            user_id = self._get_user_id(username)
        return self._make_requests_to_api("users/%s", str(user_id), "GET")

    def delete_user(self, username, user_id=None):
        if not user_id:
            user_id = self._get_user_id(username)
        # 404 means that the user does not exist anymore, so let's accept it for idempotency
        return self._make_requests_to_api(
            "users/%s", str(user_id), method="DELETE", expected_codes=[204, 404]
        )
