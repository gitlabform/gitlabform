from unittest.mock import MagicMock, patch

import pytest
from gitlab.exceptions import GitlabCreateError, GitlabGetError, GitlabUpdateError

from gitlabform.processors.project.project_pull_mirror_processor import (
    ProjectPullMirrorProcessor,
)

MIRROR_URL = "https://user:token@example.com/some/repo.git"
MASKED_MIRROR_URL = "https://*****:*****@example.com/some/repo.git"


class TestProjectPullMirrorProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = ProjectPullMirrorProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    def _project(self, existing_mirror: dict | None) -> MagicMock:
        project = MagicMock()
        if existing_mirror is None:
            # this is what GitLab actually returns when no pull mirror is configured
            project.pull_mirror.get.side_effect = GitlabGetError("The project is not mirrored", response_code=400)
        else:
            mirror = MagicMock()
            mirror.asdict.return_value = existing_mirror
            project.pull_mirror.get.return_value = mirror
        self.gl.get_project_by_path_cached.return_value = project
        return project

    def _process(self, pull_mirror: dict | None) -> None:
        self.processor._process_configuration("test/project", {"pull_mirror": pull_mirror})

    @staticmethod
    def _existing_mirror(**overrides) -> dict:
        mirror = {
            "id": 101486,
            "url": MASKED_MIRROR_URL,
            "enabled": True,
            "update_status": "finished",
            "last_error": None,
            "mirror_trigger_builds": False,
            "only_mirror_protected_branches": None,
            "mirror_overwrites_diverged_branches": None,
            "mirror_branch_regex": None,
        }
        mirror.update(overrides)
        return mirror

    # ------------------------------------------------------------------ create

    def test_creates_mirror_when_none_configured(self):
        project = self._project(None)
        config = {"url": MIRROR_URL, "enabled": True}

        self._process(config)

        project.pull_mirror.create.assert_called_once_with(config)
        project.pull_mirror.update.assert_not_called()

    def test_create_error_is_logged_and_not_raised(self, caplog):
        project = self._project(None)
        project.pull_mirror.create.side_effect = GitlabCreateError(
            "400: only_mirror_protected_branches and mirror_branch_regex cannot be used together",
            response_code=400,
        )

        with caplog.at_level("WARNING"):
            self._process({"url": MIRROR_URL, "enabled": True})

        assert "Failed to create pull mirror" in caplog.text

    def test_null_section_is_a_noop(self):
        # "pull_mirror:" without sub-keys parses to None
        project = self._project(None)

        self._process(None)

        project.pull_mirror.get.assert_not_called()
        project.pull_mirror.create.assert_not_called()
        project.pull_mirror.update.assert_not_called()
        project.pull_mirror.start.assert_not_called()

    def test_no_create_without_url_when_mirror_does_not_exist(self, caplog):
        # e.g. a baseline config of "enabled: false" applied to a project
        # that never had a pull mirror
        project = self._project(None)

        with caplog.at_level("INFO"):
            self._process({"enabled": False})

        project.pull_mirror.create.assert_not_called()
        assert "Skip configuring pull mirror" in caplog.text

    def test_get_404_is_treated_as_no_mirror(self):
        project = self._project(None)
        project.pull_mirror.get.side_effect = GitlabGetError("404 Not Found", response_code=404)
        config = {"url": MIRROR_URL, "enabled": True}

        self._process(config)

        project.pull_mirror.create.assert_called_once_with(config)

    def test_get_error_other_than_no_mirror_is_raised(self):
        project = self._project(None)
        project.pull_mirror.get.side_effect = GitlabGetError("403 Forbidden", response_code=403)

        with pytest.raises(GitlabGetError):
            self._process({"url": MIRROR_URL, "enabled": True})

        project.pull_mirror.create.assert_not_called()

    def test_get_other_400_error_is_raised(self):
        project = self._project(None)
        project.pull_mirror.get.side_effect = GitlabGetError("400 Bad Request", response_code=400)

        with pytest.raises(GitlabGetError):
            self._process({"url": MIRROR_URL, "enabled": True})

        project.pull_mirror.create.assert_not_called()

    # ------------------------------------------------------------------ update

    def test_updates_mirror_when_settings_differ(self):
        project = self._project(self._existing_mirror(mirror_trigger_builds=False))
        config = {"url": MIRROR_URL, "enabled": True, "mirror_trigger_builds": True}

        self._process(config)

        project.pull_mirror.update.assert_called_once_with(new_data=config)
        project.pull_mirror.create.assert_not_called()

    def test_no_churn_when_config_matches_existing(self, caplog):
        project = self._project(self._existing_mirror())

        with caplog.at_level("INFO"):
            self._process({"url": MIRROR_URL, "enabled": True, "mirror_trigger_builds": False})

        project.pull_mirror.update.assert_not_called()
        project.pull_mirror.create.assert_not_called()
        assert "Pull mirror remains unchanged" in caplog.text

    def test_auth_attributes_are_excluded_from_comparison(self):
        # GitLab never returns auth_user/auth_password, so they must not
        # cause an update on every run
        project = self._project(self._existing_mirror())

        self._process(
            {
                "url": MIRROR_URL,
                "enabled": True,
                "auth_user": "user",
                "auth_password": "token",
            }
        )

        project.pull_mirror.update.assert_not_called()

    def test_force_update_updates_even_when_unchanged(self, caplog):
        project = self._project(self._existing_mirror())
        config = {"url": MIRROR_URL, "enabled": True, "auth_password": "new-token"}

        with caplog.at_level("INFO"):
            self._process({**config, "force_update": True})

        project.pull_mirror.update.assert_called_once_with(new_data=config)
        assert "REMINDER: 'force_update' was used" in caplog.text

    def test_update_error_is_logged_and_not_raised(self, caplog):
        project = self._project(self._existing_mirror())
        project.pull_mirror.update.side_effect = GitlabUpdateError("400: bad request", response_code=400)

        with caplog.at_level("WARNING"):
            self._process({"url": MIRROR_URL, "enabled": False})

        assert "Failed to update pull mirror" in caplog.text

    # ------------------------------------------------------------------ sync

    def test_force_pull_triggers_sync(self):
        project = self._project(self._existing_mirror())

        self._process(
            {
                "url": MIRROR_URL,
                "enabled": True,
                "mirror_trigger_builds": False,
                "force_pull": True,
            }
        )

        project.pull_mirror.start.assert_called_once()
        project.pull_mirror.update.assert_not_called()

    def test_force_pull_alone_only_triggers_sync(self):
        project = self._project(self._existing_mirror())

        self._process({"force_pull": True})

        project.pull_mirror.start.assert_called_once()
        project.pull_mirror.create.assert_not_called()
        project.pull_mirror.update.assert_not_called()

    def test_sync_error_is_logged_and_not_raised(self, caplog):
        project = self._project(self._existing_mirror())
        project.pull_mirror.start.side_effect = GitlabCreateError("403: forbidden", response_code=403)

        with caplog.at_level("WARNING"):
            self._process({"force_pull": True})

        assert "Failed to trigger pull mirror sync" in caplog.text

    def test_force_pull_without_mirror_skips_sync(self, caplog):
        project = self._project(None)

        with caplog.at_level("INFO"):
            self._process({"force_pull": True})

        project.pull_mirror.start.assert_not_called()
        assert "Skip triggering pull mirror sync" in caplog.text

    # ------------------------------------------------------------------ diffing

    def test_get_current_state_without_mirror_is_empty(self):
        self._project(None)

        assert self.processor._get_current_state("test/project") == {}

    def test_get_desired_state_strips_gitlabform_specific_keys_and_masks_secrets(self):
        desired = self.processor._get_desired_state(
            {
                "url": MIRROR_URL,
                "enabled": True,
                "auth_password": "token",
                "force_update": True,
                "force_pull": True,
            }
        )

        # the diff is printed, so credentials must not appear in it
        assert desired == {
            "url": MASKED_MIRROR_URL,
            "enabled": True,
            "auth_password": "*****",
        }

    def test_get_desired_state_handles_null_section(self):
        assert self.processor._get_desired_state(None) == {}
