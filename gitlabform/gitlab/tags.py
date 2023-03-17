from gitlabform.gitlab.core import GitLabCore


class GitLabTags(GitLabCore):
    def get_tags(self, project_and_group_name):
        return self._make_requests_to_api(
            "projects/%s/repository/tags", project_and_group_name
        )

    def delete_tag(self, project_and_group_name, tag_name):
        self._make_requests_to_api(
            "projects/%s/repository/tags/%s",
            (project_and_group_name, tag_name),
            method="DELETE",
            expected_codes=[200, 204],
        )

    def get_protected_tags(self, project_and_group_name):
        return self._make_requests_to_api(
            "projects/%s/protected_tags",
            project_and_group_name,
        )

    def protect_tag(self, project_and_group_name, tag_name, create_access_level):
        data = {"name": tag_name}
        if create_access_level is not None:
            data["create_access_level"] = create_access_level
        return self._make_requests_to_api(
            "projects/%s/protected_tags",
            project_and_group_name,
            method="POST",
            data=data,
            expected_codes=201,
        )

    def unprotect_tag(self, project_and_group_name, tag_name):
        return self._make_requests_to_api(
            "projects/%s/protected_tags/%s",
            (project_and_group_name, tag_name),
            method="DELETE",
            expected_codes=[201, 204],
        )
