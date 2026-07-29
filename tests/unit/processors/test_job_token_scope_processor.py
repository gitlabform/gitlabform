import logging
from unittest.mock import MagicMock

from gitlab import GitlabUpdateError

from gitlabform.processors.project.job_token_scope_processor import (
    JobTokenScopeProcessor,
)


class TestJobTokenScopeProcessor:
    def setup_method(self):
        self.processor = JobTokenScopeProcessor.__new__(JobTokenScopeProcessor)

    def test__allow_push_repository_for_job_token_omitted_leaves_project_unchanged(self):
        project = MagicMock()
        project.ci_push_repository_for_job_token_allowed = False

        self.processor._process_allow_push_repository_for_job_token_setting({}, project)

        assert project.ci_push_repository_for_job_token_allowed is False
        project.save.assert_not_called()

    def test__allow_push_repository_for_job_token_matching_value_does_not_save(self):
        project = MagicMock()
        project.ci_push_repository_for_job_token_allowed = True

        self.processor._process_allow_push_repository_for_job_token_setting(
            {"allow_push_repository_for_job_token": True}, project
        )

        project.save.assert_not_called()

    def test__allow_push_repository_for_job_token_enables_and_saves(self):
        project = MagicMock()
        project.ci_push_repository_for_job_token_allowed = False

        self.processor._process_allow_push_repository_for_job_token_setting(
            {"allow_push_repository_for_job_token": True}, project
        )

        assert project.ci_push_repository_for_job_token_allowed is True
        project.save.assert_called_once_with()

    def test__allow_push_repository_for_job_token_disables_and_saves(self):
        project = MagicMock()
        project.ci_push_repository_for_job_token_allowed = True

        self.processor._process_allow_push_repository_for_job_token_setting(
            {"allow_push_repository_for_job_token": False}, project
        )

        assert project.ci_push_repository_for_job_token_allowed is False
        project.save.assert_called_once_with()

    def test__allow_push_repository_for_job_token_missing_attribute_defaults_to_false(self):
        project = MagicMock(spec=["save"])

        self.processor._process_allow_push_repository_for_job_token_setting(
            {"allow_push_repository_for_job_token": False}, project
        )

        project.save.assert_not_called()

    def test__allow_push_repository_for_job_token_update_error_warns_and_continues(self, caplog):
        project = MagicMock()
        project.ci_push_repository_for_job_token_allowed = False
        project.save.side_effect = GitlabUpdateError("unknown attribute")

        with caplog.at_level(logging.WARNING):
            self.processor._process_allow_push_repository_for_job_token_setting(
                {"allow_push_repository_for_job_token": True}, project
            )

        assert "Could not set 'allow_push_repository_for_job_token'" in caplog.text
        assert "this GitLab version may not support it" in caplog.text
        assert "unknown attribute" in caplog.text
