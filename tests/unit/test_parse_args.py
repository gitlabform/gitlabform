import sys
from unittest.mock import MagicMock, patch

from gitlabform import GitLabForm


class TestParseArgs:
    # Index in the return tuple of GitLabForm._parse_args() for
    # include_projects_scheduled_for_deletion (12 = 13th item).
    INCLUDE_SCHEDULED_FOR_DELETION_INDEX = 12

    def test__include_projects_scheduled_for_deletion__defaults_to_false(self):
        with patch.object(sys, "argv", ["gitlabform", "ALL"]):
            result = GitLabForm._parse_args()
        assert result[self.INCLUDE_SCHEDULED_FOR_DELETION_INDEX] is False

    def test__include_projects_scheduled_for_deletion__can_be_set_via_long_flag(self):
        with patch.object(sys, "argv", ["gitlabform", "ALL", "--include-projects-scheduled-for-deletion"]):
            result = GitLabForm._parse_args()
        assert result[self.INCLUDE_SCHEDULED_FOR_DELETION_INDEX] is True


class TestGitLabFormConstructorNormalMode:
    def test__include_projects_scheduled_for_deletion_propagated_from_cli(self):
        argv = ["gitlabform", "ALL", "--skip-version-check", "--include-projects-scheduled-for-deletion"]
        with (
            patch.object(sys, "argv", argv),
            patch.object(GitLabForm, "_initialize_configuration_and_gitlab", return_value=(MagicMock(), MagicMock())),
        ):
            gf = GitLabForm()
        assert gf.include_projects_scheduled_for_deletion is True
        assert gf.include_archived_projects is False


class TestGitLabFormConstructorTestMode:
    def test__include_projects_scheduled_for_deletion_propagated_from_kwarg(self):
        with patch.object(GitLabForm, "_initialize_configuration_and_gitlab", return_value=(MagicMock(), MagicMock())):
            gf = GitLabForm(
                config_string="config_version: 3\n",
                target="some_group",
                include_projects_scheduled_for_deletion=False,
            )
        assert gf.include_projects_scheduled_for_deletion is False
