from gitlabform.gitlab.core import GitLabCore


class GitlabProjectSecuritySettings(GitLabCore):
    def get_project_security_settings(self, project_and_group_name):
        security_settings = self._make_requests_to_api(
            "projects/%s/security_settings",
            project_and_group_name,
        )
        return security_settings

    def put_project_security_settings(
        self,
        project_and_group_name,
        security_settings_in_config,
    ):
        return self._make_requests_to_api(
            "projects/%s/security_settings",
            project_and_group_name,
            method="PUT",
            data=security_settings_in_config,
        )
