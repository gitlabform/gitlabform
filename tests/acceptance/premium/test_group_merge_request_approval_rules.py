import pytest

from tests.acceptance import run_gitlabform
from gitlabform.gitlab.group_merge_requests_approvals import (
    GitLabGroupMergeRequestsApprovals,
)

pytestmark = pytest.mark.requires_license


class TestGroupMergeRequestApprovalRules:
    def test__add_single_rule(self, group):

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_rules:
              any:
                approvals_required: 5
                name: "Regular approvers"
                rule_type: any_approver
        """

        run_gitlabform(config, group)
        rules = GitLabGroupMergeRequestsApprovals(
            config_string=config
        ).get_group_approval_rules(group.full_path)
        assert len(rules) >= 1

        for rule in rules:
            assert rule["name"] == "Regular approvers"
            assert rule["approvals_required"] == 5
            assert rule["rule_type"] == "any_approver"
