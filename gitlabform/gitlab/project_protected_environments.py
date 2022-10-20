from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectProtectedEnvironments(GitLabProjects):
    def list_protected_environments(self, project_and_group_name: str) -> list[dict]:
        return self._make_requests_to_api(
            "projects/%s/protected_environments", project_and_group_name
        )

    def protect_a_repository_environment(
        self, project_and_group_name: str, protected_env_cfg: dict
    ):
        return self._make_requests_to_api(
            "projects/%s/protected_environments",
            project_and_group_name,
            method="POST",
            json=protected_env_cfg,
            expected_codes=201,
        )

    def unprotect_environment(
        self, project_and_group_name: str, protected_env_cfg: dict
    ):
        return self._make_requests_to_api(
            "projects/%s/protected_environments/%s",
            (project_and_group_name, protected_env_cfg["name"]),
            method="DELETE",
            expected_codes=204,
        )
