from unittest.mock import MagicMock, patch

import pytest
from gitlab.exceptions import GitlabListError

from gitlabform.processors.group.group_ldap_links_processor import GroupLDAPLinksProcessor


class TestGroupLDAPLinksProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = GroupLDAPLinksProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    @staticmethod
    def _link(provider: str = "LDAP Main", cn=None, filter=None, group_access: int = 30) -> MagicMock:
        link = MagicMock()
        link.provider = provider
        link.cn = cn
        link.filter = filter
        link.group_access = group_access
        link.asdict.return_value = {
            "provider": provider,
            "cn": cn,
            "filter": filter,
            "group_access": group_access,
        }
        return link

    def _group(self, *links: MagicMock) -> MagicMock:
        group = MagicMock()
        group.ldap_group_links.list.return_value = list(links)
        self.gl.get_group_by_path_cached.return_value = group
        return group

    def _process(self, group_ldap_links: dict) -> None:
        self.processor._process_configuration("test/group", {"group_ldap_links": group_ldap_links})

    # ------------------------------------------------------------------ add

    def test_creates_link_when_missing(self):
        group = self._group()
        link_config = {"provider": "LDAP Main", "cn": "devops", "group_access": 40}

        self._process({"devops_users": link_config})

        group.ldap_group_links.create.assert_called_once_with(link_config)

    def test_cn_link_does_not_match_filter_link(self):
        # provider + cn and provider + filter are different identities
        existing = self._link(cn="devops")
        group = self._group(existing)
        link_config = {"provider": "LDAP Main", "filter": "(devType=security)", "group_access": 30}

        self._process({"security_users": link_config})

        group.ldap_group_links.create.assert_called_once_with(link_config)
        existing.delete.assert_not_called()

    # --------------------------------------------------------------- update

    def test_recreates_link_when_group_access_changed(self):
        existing = self._link(cn="devops", group_access=40)
        group = self._group(existing)
        link_config = {"provider": "LDAP Main", "cn": "devops", "group_access": 30}

        self._process({"devops_users": link_config})

        # the API has no update endpoint for LDAP links, so it is deleted and added again
        existing.delete.assert_called_once()
        group.ldap_group_links.create.assert_called_once_with(link_config)

    def test_no_churn_when_configured_link_matches_existing(self):
        existing = self._link(cn="devops", group_access=40)
        group = self._group(existing)

        self._process({"devops_users": {"provider": "LDAP Main", "cn": "devops", "group_access": 40}})

        existing.delete.assert_not_called()
        group.ldap_group_links.create.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_link(self):
        existing = self._link(cn="devops")
        group = self._group(existing)

        self._process({"devops_users": {"provider": "LDAP Main", "cn": "devops", "delete": True}})

        existing.delete.assert_called_once()
        group.ldap_group_links.create.assert_not_called()

    def test_delete_true_on_non_existent_is_logged_and_skipped(self, caplog):
        group = self._group()

        with caplog.at_level("INFO"):
            self._process({"devops_users": {"provider": "LDAP Main", "cn": "devops", "delete": True}})

        matching = [r for r in caplog.records if "Not deleting devops_users of group_ldap_links" in r.message]
        assert len(matching) == 1
        group.ldap_group_links.create.assert_not_called()

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_links(self):
        managed = self._link(cn="devops", group_access=40)
        stray = self._link(filter="(devType=security)")
        self._group(managed, stray)

        self._process(
            {
                "enforce": True,
                "devops_users": {"provider": "LDAP Main", "cn": "devops", "group_access": 40},
            }
        )

        stray.delete.assert_called_once()
        managed.delete.assert_not_called()

    def test_without_enforce_unmanaged_links_are_left_alone(self):
        stray = self._link(cn="stray")
        self._group(stray)

        self._process({})

        stray.delete.assert_not_called()

    # ------------------------------------------------------- empty list 404

    def test_list_404_is_treated_as_no_links(self):
        # GitLab returns 404 instead of an empty list when a group has no LDAP links
        group = self._group()
        group.ldap_group_links.list.side_effect = GitlabListError("404 Not Found", response_code=404)
        link_config = {"provider": "LDAP Main", "cn": "devops", "group_access": 40}

        self._process({"devops_users": link_config})

        group.ldap_group_links.create.assert_called_once_with(link_config)

    def test_other_list_error_is_reraised(self):
        group = self._group()
        group.ldap_group_links.list.side_effect = GitlabListError("403 Forbidden", response_code=403)

        with pytest.raises(GitlabListError):
            self._process({"devops_users": {"provider": "LDAP Main", "cn": "devops", "group_access": 40}})

        group.ldap_group_links.create.assert_not_called()
