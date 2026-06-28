from unittest.mock import MagicMock, patch

from gitlabform.processors.group.group_saml_links_processor import GroupSAMLLinksProcessor
from gitlabform.processors.util.decorators import SafeDict


class TestGroupSAMLLinksProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = GroupSAMLLinksProcessor(self.gitlab)
        self.processor.gl = MagicMock()

    @staticmethod
    def _saml_link(name: str, access_level: int) -> MagicMock:
        link = MagicMock()
        link.name = name
        link.access_level = access_level
        link.asdict.return_value = {"name": name, "access_level": access_level}
        return link

    def _group_with_links(self, *links: MagicMock) -> MagicMock:
        group = MagicMock()
        group.saml_group_links.list.return_value = list(links)
        self.processor.gl.get_group_by_path_cached.return_value = group
        return group

    def test_no_churn_when_configured_link_matches_existing(self):
        existing = self._saml_link("gitlab-test-maintainer", 40)
        group = self._group_with_links(existing)

        configuration = SafeDict(
            {
                "group_saml_links": {
                    "maintainers": {
                        "saml_group_name": "gitlab-test-maintainer",
                        "access_level": 40,
                    },
                }
            }
        )

        self.processor._process_configuration("test/group", configuration)

        group.saml_group_links.create.assert_not_called()
        existing.delete.assert_not_called()
        group.saml_group_links.delete.assert_not_called()

    def test_creates_link_when_missing(self):
        group = self._group_with_links()

        link_config = {"saml_group_name": "gitlab-test-developer", "access_level": 30}
        configuration = SafeDict({"group_saml_links": {"developers": link_config}})

        self.processor._process_configuration("test/group", configuration)

        group.saml_group_links.create.assert_called_once_with(link_config)

    def test_recreates_link_when_access_level_changes(self):
        existing = self._saml_link("gitlab-test-developer", 30)
        group = self._group_with_links(existing)

        link_config = {"saml_group_name": "gitlab-test-developer", "access_level": 40}
        configuration = SafeDict({"group_saml_links": {"developers": link_config}})

        self.processor._process_configuration("test/group", configuration)

        existing.delete.assert_called_once()
        group.saml_group_links.create.assert_called_once_with(link_config)

    def test_enforce_deletes_unconfigured_links(self):
        kept = self._saml_link("gitlab-test-maintainer", 40)
        stray = self._saml_link("gitlab-stray", 20)
        group = self._group_with_links(kept, stray)

        configuration = SafeDict(
            {
                "group_saml_links": {
                    "enforce": True,
                    "maintainers": {
                        "saml_group_name": "gitlab-test-maintainer",
                        "access_level": 40,
                    },
                }
            }
        )

        self.processor._process_configuration("test/group", configuration)

        group.saml_group_links.delete.assert_called_once_with("gitlab-stray")
        # the matching link must not churn
        kept.delete.assert_not_called()
        group.saml_group_links.create.assert_not_called()
