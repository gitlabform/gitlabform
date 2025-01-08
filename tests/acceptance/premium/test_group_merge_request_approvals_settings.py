import pytest

from tests.acceptance import run_gitlabform
from gitlabform.gitlab.group_merge_requests_approvals import (
    GitLabGroupMergeRequestsApprovals,
)

pytestmark = pytest.mark.requires_license


class TestGroupMergeRequestApprovalsSettings:
    def test__edit_settings(self, group):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_settings:
              retain_approvals_on_push: false
              allow_overrides_to_approver_list_per_merge_request: false
              allow_committer_approval: false
              allow_author_approval: false
        """

        run_gitlabform(config, group)

        settings = GitLabGroupMergeRequestsApprovals(
            config_string=config
        ).get_group_approvals_settings(group.full_path)

        assert settings["retain_approvals_on_push"]["value"] is False
        assert (
            settings["allow_overrides_to_approver_list_per_merge_request"]["value"]
            is False
        )
        assert settings["allow_committer_approval"]["value"] is False
        assert settings["allow_author_approval"]["value"] is False

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_settings:
              retain_approvals_on_push: true
              allow_overrides_to_approver_list_per_merge_request: true
              allow_committer_approval: true
              allow_author_approval: true
        """

        run_gitlabform(config, group)

        settings = GitLabGroupMergeRequestsApprovals(
            config_string=config
        ).get_group_approvals_settings(group.full_path)

        assert settings["retain_approvals_on_push"]["value"] is True
        assert (
            settings["allow_overrides_to_approver_list_per_merge_request"]["value"]
            is True
        )
        assert settings["allow_committer_approval"]["value"] is True
        assert settings["allow_author_approval"]["value"] is True
