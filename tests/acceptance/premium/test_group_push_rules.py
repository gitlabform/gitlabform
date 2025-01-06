import pytest
from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestGroupPushRules:
    def test__create_group_push_rules(self, group):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_push_rules:
              commit_message_regex: ''
              member_check: false
              commit_committer_check: true
              commit_committer_name_check: true
        """

        run_gitlabform(config, group)

        push_rules = group.pushrules.get()
        assert push_rules.commit_message_regex == ""
        assert push_rules.member_check is False
        assert push_rules.commit_committer_check is True
        assert push_rules.commit_committer_name_check is True

    def test__edit_group_push_rules(self, group):
        self.test__create_group_push_rules(group)

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_push_rules:
              commit_message_regex: ''
              member_check: true
              commit_committer_check: false
              commit_committer_name_check: false
        """

        run_gitlabform(config, group)

        push_rules = group.pushrules.get()
        assert push_rules.commit_message_regex == ""
        assert push_rules.member_check is True
        assert push_rules.commit_committer_check is False
        assert push_rules.commit_committer_name_check is False
