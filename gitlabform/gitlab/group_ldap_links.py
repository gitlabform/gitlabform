import cli_ui

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab.core import NotFoundException, InvalidParametersException
from gitlabform.gitlab.groups import GitLabGroups


class GitLabGroupLDAPLinks(GitLabGroups):
    def get_ldap_group_links(self, group):
        group_id = self.get_group_id_case_insensitive(group)
        return self._make_requests_to_api(
            "groups/%s/ldap_group_links", group_id, expected_codes=[200, 404]
        )

    def add_ldap_group_link(self, group, data):
        group_id = self.get_group_id_case_insensitive(group)
        data["id"] = group_id

        # this is a GitLab API bug - it returns 404 here instead of 400 for bad requests...
        try:
            return self._make_requests_to_api(
                "groups/%s/ldap_group_links",
                group_id,
                method="POST",
                data=data,
                expected_codes=[200, 201],
            )
        except NotFoundException:
            cli_ui.fatal(
                f"Invalid parameters for LDAP group link for group {group} - {data} ",
                exit_code=EXIT_INVALID_INPUT,
            )

    def delete_ldap_group_link(self, group, data):
        if "group_access" in data:
            del data["group_access"]

        group_id = self.get_group_id_case_insensitive(group)
        data["id"] = group_id

        # 404 means that the LDAP group link is already removed, so let's accept it for idempotency
        self._make_requests_to_api(
            "groups/%s/ldap_group_links",
            group_id,
            method="DELETE",
            data=data,
            expected_codes=[204, 404],
        )
