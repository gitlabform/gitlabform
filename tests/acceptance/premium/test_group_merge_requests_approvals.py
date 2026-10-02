from typing import Any, cast

import pytest

from tests.acceptance import gl, run_gitlabform

pytestmark = pytest.mark.requires_license


def get_group_merge_requests_approvals(group) -> dict:
    # python-gitlab does not support this API yet, see the processor for details
    settings = cast(dict[str, Any], gl.http_get(f"/groups/{group.id}/merge_request_approval_setting"))
    return {key: setting["value"] for key, setting in settings.items()}


class TestGroupMergeRequestsApprovals:
    def test__edit_settings(self, group):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approvals:
              allow_author_approval: false
              allow_committer_approval: false
              allow_overrides_to_approver_list_per_merge_request: false
              retain_approvals_on_push: true
        """

        run_gitlabform(config, group)

        settings = get_group_merge_requests_approvals(group)
        assert settings["allow_author_approval"] is False
        assert settings["allow_committer_approval"] is False
        assert settings["allow_overrides_to_approver_list_per_merge_request"] is False
        assert settings["retain_approvals_on_push"] is True

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approvals:
              allow_author_approval: true
              allow_committer_approval: true
              allow_overrides_to_approver_list_per_merge_request: true
              retain_approvals_on_push: false
        """

        run_gitlabform(config, group)

        settings = get_group_merge_requests_approvals(group)
        assert settings["allow_author_approval"] is True
        assert settings["allow_committer_approval"] is True
        assert settings["allow_overrides_to_approver_list_per_merge_request"] is True
        assert settings["retain_approvals_on_push"] is False
