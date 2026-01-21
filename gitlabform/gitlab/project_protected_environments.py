from cli_ui import debug

from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectProtectedEnvironments(GitLabProjects):
    def list_protected_environments(self, project_and_group_name: str):
        return self._make_requests_to_api("projects/%s/protected_environments", project_and_group_name)

    def protect_a_repository_environment(
        self, project_and_group_name: str, protected_env_cfg: dict, retry: bool = True
    ):
        response = self._make_requests_to_api(
            "projects/%s/protected_environments",
            project_and_group_name,
            method="POST",
            json=protected_env_cfg,
            expected_codes=201,
        )

        # TODO: remove this when this issue is resolved -> https://gitlab.com/gitlab-org/gitlab/-/issues/378657
        if retry and (len(protected_env_cfg["deploy_access_levels"]) != len(response["deploy_access_levels"])):
            debug(f'Gitlab\'s returned "deploy_access_levels" differs from the sent cfg, trying again...')

            self.unprotect_environment(project_and_group_name, protected_env_cfg)

            return self.protect_a_repository_environment(project_and_group_name, protected_env_cfg, False)

        return response

    def unprotect_environment(self, project_and_group_name: str, protected_env_cfg: dict):
        return self._make_requests_to_api(
            "projects/%s/protected_environments/%s",
            (project_and_group_name, protected_env_cfg["name"]),
            method="DELETE",
            expected_codes=204,
        )
