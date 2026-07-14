from unittest.mock import MagicMock

import pytest
from gitlab.v4.objects import Group, Project

from gitlabform.processors.util.badges_processor import BadgesProcessor


class TestBadgesProcessor:
    def setup_method(self):
        self.helper = BadgesProcessor()

    @staticmethod
    def _badge(name: str, kind: str = "project", **fields) -> MagicMock:
        badge = MagicMock()
        badge.name = name
        badge.kind = kind
        for key, value in fields.items():
            setattr(badge, key, value)
        badge.asdict.return_value = {"name": name, "kind": kind, **fields}
        return badge

    @staticmethod
    def _project(*badges: MagicMock) -> MagicMock:
        project = MagicMock()
        project.__class__ = Project  # type: ignore[assignment]  # satisfy isinstance() in the helper
        project.path_with_namespace = "test/project"
        project.badges.list.return_value = list(badges)
        return project

    @staticmethod
    def _group(*badges: MagicMock) -> MagicMock:
        group = MagicMock()
        group.__class__ = Group  # type: ignore[assignment]
        group.full_path = "test/group"
        del group.path_with_namespace  # force the helper to fall back to full_path
        group.badges.list.return_value = list(badges)
        return group

    @staticmethod
    def _needs_update(return_value: bool) -> MagicMock:
        return MagicMock(return_value=return_value)

    # ------------------------------------------------------------------ add

    def test_creates_badge_when_missing(self):
        project = self._project()
        badge_config = {
            "name": "ci",
            "link_url": "https://example.com/link",
            "image_url": "https://example.com/img.svg",
        }

        self.helper.process_badges(
            "badges",
            {"my-badge": badge_config},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        project.badges.create.assert_called_once_with(badge_config)

    # --------------------------------------------------------------- update

    def test_updates_badge_via_save_when_needs_update(self):
        existing = self._badge("ci", link_url="https://old", image_url="https://img")
        project = self._project(existing)
        badge_config = {
            "name": "ci",
            "link_url": "https://new",
            "image_url": "https://img",
        }

        self.helper.process_badges(
            "badges",
            {"my-badge": badge_config},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(True),
        )

        # setattr wrote the new values back onto the object before save()
        assert existing.link_url == "https://new"
        assert existing.image_url == "https://img"
        existing.save.assert_called_once()
        project.badges.create.assert_not_called()
        existing.delete.assert_not_called()

    def test_no_churn_when_configured_badge_matches_existing(self):
        existing = self._badge("ci", link_url="https://x", image_url="https://y")
        project = self._project(existing)
        badge_config = {
            "name": "ci",
            "link_url": "https://x",
            "image_url": "https://y",
        }

        self.helper.process_badges(
            "badges",
            {"my-badge": badge_config},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        existing.save.assert_not_called()
        existing.delete.assert_not_called()
        project.badges.create.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_badge(self):
        existing = self._badge("ci")
        project = self._project(existing)

        self.helper.process_badges(
            "badges",
            {"my-badge": {"name": "ci", "delete": True}},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        existing.delete.assert_called_once()
        project.badges.create.assert_not_called()

    def test_delete_true_on_non_existent_is_noop(self):
        project = self._project()

        self.helper.process_badges(
            "badges",
            {"my-badge": {"name": "ci", "delete": True}},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        project.badges.create.assert_not_called()

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_badges(self):
        managed = self._badge("ci", link_url="https://x", image_url="https://y")
        stray = self._badge("stray")
        project = self._project(managed, stray)

        self.helper.process_badges(
            "badges",
            {
                "my-badge": {
                    "name": "ci",
                    "link_url": "https://x",
                    "image_url": "https://y",
                }
            },
            enforce=True,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        stray.delete.assert_called_once()
        managed.delete.assert_not_called()

    # ----------------------------------------------------- project/group filter

    def test_project_filters_inherited_group_kind_badges_out_of_enforce(self):
        # Only project-kind badges should be touched; inherited group badges are ignored.
        project_badge = self._badge("proj-badge", kind="project")
        inherited = self._badge("inherited-group-badge", kind="group")
        project = self._project(project_badge, inherited)

        self.helper.process_badges(
            "badges",
            {},
            enforce=True,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        project_badge.delete.assert_called_once()
        inherited.delete.assert_not_called()

    def test_group_does_not_filter_by_kind(self):
        # For groups the endpoint only returns group-scoped badges, so no filter is applied.
        group_badge = self._badge("gb")
        group = self._group(group_badge)

        self.helper.process_badges(
            "group_badges",
            {},
            enforce=True,
            group_or_project=group,
            needs_update=self._needs_update(False),
        )

        group_badge.delete.assert_called_once()

    # ------------------------------------------------------------ validation

    def test_missing_name_exits(self):
        project = self._project()

        with pytest.raises(SystemExit):
            self.helper.process_badges(
                "badges",
                {"my-badge": {"link_url": "https://x", "image_url": "https://y"}},
                enforce=False,
                group_or_project=project,
                needs_update=self._needs_update(False),
            )
        project.badges.create.assert_not_called()

    def test_duplicate_names_exit_before_any_api_call(self):
        project = self._project()

        with pytest.raises(SystemExit):
            self.helper.process_badges(
                "badges",
                {
                    "a": {"name": "dup", "link_url": "https://x", "image_url": "https://y"},
                    "b": {"name": "dup", "link_url": "https://z", "image_url": "https://w"},
                },
                enforce=False,
                group_or_project=project,
                needs_update=self._needs_update(False),
            )
        project.badges.list.assert_not_called()

    def test_missing_link_url_exits(self):
        project = self._project()

        with pytest.raises(SystemExit):
            self.helper.process_badges(
                "badges",
                {"my-badge": {"name": "ci", "image_url": "https://y"}},
                enforce=False,
                group_or_project=project,
                needs_update=self._needs_update(False),
            )
        project.badges.create.assert_not_called()

    def test_missing_image_url_exits(self):
        project = self._project()

        with pytest.raises(SystemExit):
            self.helper.process_badges(
                "badges",
                {"my-badge": {"name": "ci", "link_url": "https://x"}},
                enforce=False,
                group_or_project=project,
                needs_update=self._needs_update(False),
            )
        project.badges.create.assert_not_called()

    def test_delete_true_bypasses_required_fields_validation(self):
        # A delete-only entry doesn't need link_url / image_url.
        existing = self._badge("ci")
        project = self._project(existing)

        self.helper.process_badges(
            "badges",
            {"my-badge": {"name": "ci", "delete": True}},
            enforce=False,
            group_or_project=project,
            needs_update=self._needs_update(False),
        )

        existing.delete.assert_called_once()
