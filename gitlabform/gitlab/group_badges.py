from gitlabform.gitlab.core import InvalidParametersException
from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupBadges(GitLabGroups):
    def get_group_badges(self, group_path):
        # (unlike the one for project badges) this endpoint returns ONLY group badges
        return self._make_requests_to_api(
            "groups/%s/badges",
            group_path,
            expected_codes=200,
        )

    # def get_group_badge(
    #     self,
    #     group_path,
    #     badge_id,
    # ):
    #     return self._make_requests_to_api(
    #         "groups/%s/badges/%", (group_path, badge_id)
    #     )

    def add_group_badge(
        self,
        group_path,
        badge_in_config,
    ):
        self._validate_group_badges_call(badge_in_config)
        self._validate_add_and_edit_group_badges_calls(badge_in_config)

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
        self._validate_group_badges_call(badge_in_config)
        self._validate_add_and_edit_group_badges_calls(badge_in_config)

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
        self._validate_group_badges_call(badge_in_gitlab)
        # 404 means it is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "groups/%s/badges/%s",
            (group_path, badge_in_gitlab["id"]),
            method="DELETE",
            expected_codes=[200, 204, 404],
        )

    # TODO: deduplicate this and the various keys in BadgesProcessor(MultipleEntitiesProcessor)
    @staticmethod
    def _validate_group_badges_call(badge_data):
        if not badge_data.get("name", None):
            raise InvalidParametersException("Name of a group badge has to be defined.")

    # TODO: deduplicate this and the various keys in BadgesProcessor(MultipleEntitiesProcessor)
    @staticmethod
    def _validate_add_and_edit_group_badges_calls(badge_data):
        if not badge_data.get("link_url", None) or not badge_data.get(
            "image_url", None
        ):
            raise InvalidParametersException(
                "link_url and image_url of a group badge have to be defined."
            )
