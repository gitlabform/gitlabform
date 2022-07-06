from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectBadges(GitLabProjects):
    def get_project_badges(self, project_and_group_name):
        badges = self._make_requests_to_api(
            "projects/%s/badges",
            project_and_group_name,
            expected_codes=200,
        )
        # according to the docs_new this endpoint returns also the group badges
        # but we want only the project badges here
        return [badge for badge in badges if badge["kind"] == "project"]

    def add_project_badge(
        self,
        project_and_group_name,
        badge_in_config,
    ):
        return self._make_requests_to_api(
            "projects/%s/badges",
            project_and_group_name,
            method="POST",
            data=badge_in_config,
            expected_codes=201,
        )

    def edit_project_badge(
        self,
        project_and_group_name,
        badge_in_gitlab,
        badge_in_config,
    ):
        return self._make_requests_to_api(
            "projects/%s/badges/%s",
            (project_and_group_name, badge_in_gitlab["id"]),
            method="PUT",
            data=badge_in_config,
        )

    def delete_project_badge(
        self,
        project_and_group_name,
        badge_in_gitlab,
    ):
        # 404 means it is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "projects/%s/badges/%s",
            (project_and_group_name, badge_in_gitlab["id"]),
            method="DELETE",
            expected_codes=[200, 204, 404],
        )
