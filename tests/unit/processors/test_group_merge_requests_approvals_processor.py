from unittest.mock import MagicMock, patch

from gitlabform.processors.group.group_merge_requests_approvals_processor import (
    GroupMergeRequestsApprovalsProcessor,
)
from gitlabform.processors.util.decorators import SafeDict

API_PATH = "/groups/42/merge_request_approval_setting"


def settings_in_gitlab(**overrides) -> dict:
    settings = {
        "allow_author_approval": True,
        "allow_committer_approval": True,
        "allow_overrides_to_approver_list_per_merge_request": True,
        "retain_approvals_on_push": False,
        "selective_code_owner_removals": False,
        "require_password_to_approve": False,
        "require_reauthentication_to_approve": False,
    }
    settings.update(overrides)
    return {key: {"value": value, "locked": False, "inherited_from": None} for key, value in settings.items()}


class TestGroupMergeRequestsApprovalsProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = GroupMergeRequestsApprovalsProcessor(self.gitlab)
        self.processor.gl = MagicMock()

        group = MagicMock()
        group.id = 42
        self.processor.gl.get_group_by_path_cached.return_value = group
        self.group = group

    def test_updates_settings_when_they_differ(self):
        self.processor.gl.http_get.return_value = settings_in_gitlab()

        configuration = SafeDict(
            {
                "group_merge_requests_approvals": {
                    "allow_author_approval": False,
                    "retain_approvals_on_push": True,
                }
            }
        )

        self.processor._process_configuration("test/group", configuration)

        self.processor.gl.http_get.assert_called_once_with(API_PATH)
        self.processor.gl.http_put.assert_called_once_with(
            API_PATH,
            post_data={
                "allow_author_approval": False,
                "retain_approvals_on_push": True,
            },
        )

    def test_no_update_when_settings_already_match(self):
        self.processor.gl.http_get.return_value = settings_in_gitlab(
            allow_author_approval=False, retain_approvals_on_push=True
        )

        configuration = SafeDict(
            {
                "group_merge_requests_approvals": {
                    "allow_author_approval": False,
                    "retain_approvals_on_push": True,
                }
            }
        )

        self.processor._process_configuration("test/group", configuration)

        self.processor.gl.http_put.assert_not_called()

    def test_current_state_for_diff_contains_plain_values(self):
        self.processor.gl.http_get.return_value = settings_in_gitlab(selective_code_owner_removals=True)

        current_state = self.processor._get_current_state("test/group")

        self.processor.gl.http_get.assert_called_once_with(API_PATH)
        assert current_state == {
            "allow_author_approval": True,
            "allow_committer_approval": True,
            "allow_overrides_to_approver_list_per_merge_request": True,
            "retain_approvals_on_push": False,
            "selective_code_owner_removals": True,
            "require_password_to_approve": False,
            "require_reauthentication_to_approve": False,
        }
