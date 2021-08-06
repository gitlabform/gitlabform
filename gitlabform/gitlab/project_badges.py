from gitlabform.gitlab.core import InvalidParametersException
from gitlabform.gitlab.projects import GitLabProjects


class GitLabProjectBadges(GitLabProjects):
    def get_project_badges(self, project_and_group_name):
        badges = self._make_requests_to_api(
            "projects/%s/badges",
            project_and_group_name,
            expected_codes=200,
        )
        # according to the docs this endpoint returns also the group badges
        # but we want only the project badges here
        return [badge for badge in badges if badge["kind"] == "project"]

    # def get_project_badge(
    #     self,
    #     project_and_group_name,
    #     badge_id,
    # ):
    #     return self._make_requests_to_api(
    #         "projects/%s/badges/%", (project_and_group_name, badge_id)
    #     )

    def add_project_badge(
        self,
        project_and_group_name,
        badge_in_config,
    ):
        self._validate_project_badges_call(badge_in_config)
        self._validate_add_and_edit_project_badges_calls(badge_in_config)

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
        self._validate_project_badges_call(badge_in_config)
        self._validate_add_and_edit_project_badges_calls(badge_in_config)

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
        self._validate_project_badges_call(badge_in_gitlab)
        # 404 means it is already removed, so let's accept it for idempotency
        return self._make_requests_to_api(
            "projects/%s/badges/%s",
            (project_and_group_name, badge_in_gitlab["id"]),
            method="DELETE",
            expected_codes=[200, 204, 404],
        )

    # TODO: deduplicate this and the various keys in BadgesProcessor(MultipleEntitiesProcessor)
    @staticmethod
    def _validate_project_badges_call(badge_data):
        if not badge_data.get("name", None):
            raise InvalidParametersException(
                "Name of a project badge has to be defined."
            )

    # TODO: deduplicate this and the various keys in BadgesProcessor(MultipleEntitiesProcessor)
    @staticmethod
    def _validate_add_and_edit_project_badges_calls(badge_data):
        if not badge_data.get("link_url", None) or not badge_data.get(
            "image_url", None
        ):
            raise InvalidParametersException(
                "link_url and image_url of a project badge have to be defined."
            )
