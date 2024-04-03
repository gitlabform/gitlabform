from gitlabform.gitlab.core import NotFoundException, InvalidParametersException
from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupSAMLLinks(GitLabGroups):
    def get_saml_group_links(self, group):
        group_id = self.get_group_id_case_insensitive(group)
        return self._make_requests_to_api(
            "groups/%s/saml_group_links", group_id, expected_codes=[200, 404]
        )

    def add_saml_group_link(self, group, data):
        group_id = self.get_group_id_case_insensitive(group)
        data["id"] = group_id

        try:
            return self._make_requests_to_api(
                "groups/%s/saml_group_links",
                group_id,
                method="POST",
                data=data,
                expected_codes=[200, 201],
            )
        # this is a GitLab API bug - it returns 404 here instead of 400 for bad requests...
        except NotFoundException:
            raise InvalidParametersException(
                f"Invalid parameters for a Group SAML link for group {group}: {data}"
            )

    def delete_saml_group_link(self, group, data):
        if "group_access" in data:
            del data["group_access"]

        group_id = self.get_group_id_case_insensitive(group)
        data["id"] = group_id

        # 404 means that the SAML group link is already removed, so let's accept it for idempotency
        self._make_requests_to_api(
            "groups/%s/saml_group_links",
            group_id,
            method="DELETE",
            data=data,
            expected_codes=[204, 404],
        )
