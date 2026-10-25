from unittest.mock import MagicMock, patch

import pytest
from gitlab import GitlabDeleteError

from gitlabform.processors.project.members_processor import MembersProcessor


class TestMembersProcessorGroups:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = MembersProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    def _project(self, *shared_with_groups: dict) -> MagicMock:
        project = MagicMock()
        project.id = 42
        self.gl.get_project_by_path_cached.return_value = project
        # the shared groups are fetched fresh, not from the cached project object
        fresh_project = MagicMock()
        fresh_project.shared_with_groups = list(shared_with_groups)
        self.gl.projects.get.return_value = fresh_project
        return project

    @staticmethod
    def _shared_group(full_path: str, group_access_level: int = 30, expires_at=None) -> dict:
        return {
            "group_full_path": full_path,
            "group_access_level": group_access_level,
            "expires_at": expires_at,
        }

    def _process_groups(self, groups: dict, enforce: bool = False) -> None:
        self.processor._process_groups("test/project", groups, enforce)

    def test_shares_group_when_not_a_member(self):
        project = self._project()
        self.gl.get_group_id.return_value = 7

        self._process_groups({"some/group": {"group_access": 30}})

        project.share.assert_called_once_with(7, 30, None)

    def test_reshares_group_when_access_level_differs(self):
        project = self._project(self._shared_group("some/group", group_access_level=10))
        self.gl.get_group_id.return_value = 7
        order = MagicMock()
        order.attach_mock(project.unshare, "unshare")
        order.attach_mock(project.share, "share")

        self._process_groups({"some/group": {"group_access": 30}})

        # the group access is removed first and then re-added, to ensure the expected access level
        assert [name for name, args, kwargs in order.mock_calls] == ["unshare", "share"]

    def test_skips_group_that_already_has_the_configured_settings(self):
        project = self._project(self._shared_group("some/group", group_access_level=30))

        self._process_groups({"some/group": {"group_access": 30}})

        project.share.assert_not_called()
        project.unshare.assert_not_called()

    def test_enforce_removes_groups_not_in_config(self):
        project = self._project(self._shared_group("stray/group"))
        self.gl.get_group_id.return_value = 9

        self._process_groups({}, enforce=True)

        project.unshare.assert_called_once_with(9)

    def test_without_enforce_groups_not_in_config_are_left_alone(self):
        project = self._project(self._shared_group("stray/group"))

        self._process_groups({})

        project.unshare.assert_not_called()

    def test_unshare_of_a_not_shared_group_is_tolerated(self):
        project = self._project(self._shared_group("some/group", group_access_level=10))
        self.gl.get_group_id.return_value = 7
        project.unshare.side_effect = GitlabDeleteError("404 Not Found", response_code=404)

        self._process_groups({"some/group": {"group_access": 30}})

        project.share.assert_called_once_with(7, 30, None)

    def test_other_unshare_error_is_reraised(self):
        project = self._project(self._shared_group("some/group", group_access_level=10))
        self.gl.get_group_id.return_value = 7
        project.unshare.side_effect = GitlabDeleteError("403 Forbidden", response_code=403)

        with pytest.raises(GitlabDeleteError):
            self._process_groups({"some/group": {"group_access": 30}})

        project.share.assert_not_called()

    def test_group_with_uppercase_path_in_gitlab_is_matched_and_kept(self):
        # the config side is compared in lowercase, so the GitLab side must be too
        project = self._project(self._shared_group("MyTeam/Sub", group_access_level=30))

        self._process_groups({"myteam/sub": {"group_access": 30}}, enforce=True)

        project.share.assert_not_called()
        project.unshare.assert_not_called()
