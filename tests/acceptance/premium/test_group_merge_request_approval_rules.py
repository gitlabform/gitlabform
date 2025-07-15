import pytest

from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestGroupMergeRequestApprovalRules:
    def test__add_single_rule(self, group):

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_rules:
              any:
                approvals_required: 5
                rule_type: regular
                name: "Any Approver"
        """

        run_gitlabform(config, group)
        rules = group.approval_rules.list()
        assert len(rules) == 1

        for rule in rules:
            assert rule.name == "Any Approver"
            assert rule.approvals_required == 5
            assert rule.rule_type == "regular"

    def test__edit_rule(self, group):

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_rules:
              any:
                approvals_required: 1
                rule_type: any_approver
                name: "Any Approver"
        """

        run_gitlabform(config, group)
        rules = group.approval_rules.list()
        assert len(rules) == 1
        assert rules[0].name == "Any Approver"
        assert rules[0].approvals_required == 1
        assert rules[0].rule_type == "any_approver"

    def test__add_multiple_rules(self, group):

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_merge_requests_approval_rules:
              any:
                approvals_required: 1
                rule_type: any_approver
                name: "Any Approver"
              any1:
                approvals_required: 1
                rule_type: regular
                name: "Regular"
        """

        run_gitlabform(config, group)
        rules = group.approval_rules.list()
        assert len(rules) == 2
        assert rules[1].name == "Regular"
        assert rules[1].approvals_required == 1
        assert rules[1].rule_type == "regular"
