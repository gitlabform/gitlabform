from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupBadges(GitLabGroups):
    def get_group_badges(self, group_path):
        # (unlike the one for project badges) this endpoint returns ONLY group badges
        return self._make_requests_to_api(
            "groups/%s/badges",
            group_path,
            expected_codes=200,
        )

    def add_group_badge(
        self,
        group_path,
        badge_in_config,
    ):
        return self._make_requests_to_api(
            "groups/%s/badges",
            group_path,
            method="POST",
            data=badge_in_config,
            expected_codes=201,
        )

    def edit_group_badge(
        self,
        group_path,
        badge_in_gitlab,
        badge_in_config,
    ):
        return self._make_requests_to_api(
            "groups/%s/badges/%s",
            (group_path, badge_in_gitlab["id"]),
            method="PUT",
            data=badge_in_config,
        )

    def delete_group_badge(
        self,
        group_path,
        badge_in_gitlab,
    ):
        # 404 means it is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s/badges/%s",
            (group_path, badge_in_gitlab["id"]),
            method="DELETE",
            expected_codes=[200, 204, 404],
        )
