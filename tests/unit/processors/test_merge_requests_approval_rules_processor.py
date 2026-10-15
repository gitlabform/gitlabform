from unittest.mock import MagicMock, patch

import pytest
from gitlab.exceptions import GitlabGetError

from gitlabform.processors.project.merge_requests_approval_rules import MergeRequestsApprovalRules


class TestMergeRequestsApprovalRulesProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = MergeRequestsApprovalRules(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    @staticmethod
    def _rule(name: str = "standard", approvals_required: int = 1, rule_id: int = 1, **fields) -> MagicMock:
        rule = MagicMock()
        rule.name = name
        rule.id = rule_id
        rule.asdict.return_value = {
            "id": rule_id,
            "name": name,
            "rule_type": "regular",
            "approvals_required": approvals_required,
            "users": [],
            "groups": [],
            "protected_branches": [],
            **fields,
        }
        return rule

    @staticmethod
    def _branch(name: str, branch_id: int) -> MagicMock:
        branch = MagicMock()
        branch.name = name
        branch.id = branch_id
        return branch

    def _project(self, *rules: MagicMock) -> MagicMock:
        project = MagicMock()
        project.approvalrules.list.return_value = list(rules)
        self.gl.get_project_by_path_cached.return_value = project
        return project

    def _process(self, merge_requests_approval_rules: dict) -> None:
        self.processor._process_configuration(
            "test/project", {"merge_requests_approval_rules": merge_requests_approval_rules}
        )

    # ------------------------------------------------------------------ add

    def test_creates_rule_when_missing(self):
        project = self._project()
        rule_config = {"name": "standard", "approvals_required": 2, "user_ids": [5]}

        self._process({"default": rule_config})

        project.approvalrules.create.assert_called_once_with(rule_config)

    def test_protected_branches_are_converted_to_ids_on_create(self):
        project = self._project()
        project.protectedbranches.list.return_value = [self._branch("main", 42)]

        self._process({"default": {"name": "standard", "approvals_required": 1, "protected_branches": ["main"]}})

        project.approvalrules.create.assert_called_once_with(
            {"name": "standard", "approvals_required": 1, "protected_branch_ids": [42]}
        )

    def test_branches_are_resolved_with_a_single_list_call(self):
        project = self._project()
        project.protectedbranches.list.return_value = [self._branch("main", 42), self._branch("release", 43)]

        self._process(
            {
                "first": {"name": "first", "approvals_required": 1, "protected_branches": ["main"]},
                "second": {"name": "second", "approvals_required": 2, "protected_branches": ["main", "release"]},
            }
        )

        project.protectedbranches.list.assert_called_once()

    def test_no_branch_lookup_when_no_protected_branches_configured(self):
        project = self._project()

        self._process({"default": {"name": "standard", "approvals_required": 1}})

        project.protectedbranches.list.assert_not_called()

    # --------------------------------------------------------------- update

    def test_updates_rule_when_approvals_required_changed(self):
        existing = self._rule("standard", approvals_required=1, rule_id=7)
        project = self._project(existing)

        self._process({"default": {"name": "standard", "approvals_required": 2}})

        # the API supports updates, so the rule is edited in place instead of recreated
        existing.delete.assert_not_called()
        project.approvalrules.update.assert_called_once_with(
            7,
            {
                "name": "standard",
                "approvals_required": 2,
                "user_ids": [],
                "group_ids": [],
                "protected_branch_ids": [],
            },
        )

    def test_update_clears_lists_omitted_in_config(self):
        # GitLab treats omitted user_ids/group_ids/protected_branch_ids as "no change",
        # so the processor must send empty lists to make removals in config take effect
        existing = self._rule("standard", rule_id=7, users=[{"id": 5, "username": "alice"}])
        project = self._project(existing)

        self._process({"default": {"name": "standard", "approvals_required": 1}})

        payload = project.approvalrules.update.call_args[0][1]
        assert payload["user_ids"] == []
        assert payload["group_ids"] == []
        assert payload["protected_branch_ids"] == []

    def test_no_churn_when_configured_rule_matches_existing(self):
        existing = self._rule("standard", approvals_required=2, users=[{"id": 5, "username": "alice"}])
        project = self._project(existing)

        self._process({"default": {"name": "standard", "approvals_required": 2, "user_ids": [5]}})

        project.approvalrules.update.assert_not_called()
        project.approvalrules.create.assert_not_called()

    def test_delete_false_is_ignored_and_not_sent_to_the_api(self):
        # "delete" is a gitlabform control key: an explicit "delete: false" must not
        # trigger an update on every run, nor end up in the API payload
        existing = self._rule("standard", approvals_required=2, rule_id=7)
        project = self._project(existing)

        self._process({"default": {"name": "standard", "approvals_required": 2, "delete": False}})

        project.approvalrules.update.assert_not_called()
        project.approvalrules.create.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_rule(self):
        existing = self._rule("standard")
        project = self._project(existing)

        self._process({"default": {"name": "standard", "delete": True}})

        existing.delete.assert_called_once()
        project.approvalrules.create.assert_not_called()

    def test_delete_true_on_non_existent_is_logged_and_skipped(self, caplog):
        project = self._project()

        with caplog.at_level("INFO"):
            self._process({"default": {"name": "standard", "delete": True}})

        matching = [r for r in caplog.records if "Not deleting default of merge_requests_approval_rules" in r.message]
        assert len(matching) == 1
        project.approvalrules.create.assert_not_called()

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_rules_before_adding(self):
        # stale rules are deleted first, so that unique-constraint slots
        # (e.g. only one any_approver rule per project) are freed for new rules
        stray = self._rule("Any approver", rule_id=9)
        project = self._project(stray)
        order = MagicMock()
        order.attach_mock(stray.delete, "stray_delete")
        order.attach_mock(project.approvalrules.create, "create")

        self._process(
            {
                "enforce": True,
                "default": {"name": "replacement", "approvals_required": 1, "rule_type": "any_approver"},
            }
        )

        assert [name for name, args, kwargs in order.mock_calls] == ["stray_delete", "create"]

    def test_enforce_does_not_delete_when_branch_resolution_fails(self):
        # branch names are resolved before anything is deleted, so a bad branch name
        # in the config cannot leave the project without approval rules
        stray = self._rule("stray")
        project = self._project(stray)
        project.protectedbranches.list.return_value = [self._branch("main", 42)]

        with pytest.raises(GitlabGetError, match="typo"):
            self._process(
                {
                    "enforce": True,
                    "default": {"name": "new", "approvals_required": 1, "protected_branches": ["typo"]},
                }
            )

        stray.delete.assert_not_called()
        project.approvalrules.create.assert_not_called()

    def test_without_enforce_unmanaged_rules_are_left_alone(self):
        stray = self._rule("stray")
        self._project(stray)

        self._process({})

        stray.delete.assert_not_called()

    def test_enforce_is_not_removed_from_the_shared_configuration(self):
        # the configuration dict is reused when processing is retried, so a run must not mutate it
        stray = self._rule("stray")
        self._project(stray)
        configuration = {"merge_requests_approval_rules": {"enforce": True}}

        self.processor._process_configuration("test/project", configuration)

        stray.delete.assert_called_once()
        assert configuration["merge_requests_approval_rules"] == {"enforce": True}

    # ------------------------------------------------------- _needs_update

    @staticmethod
    def _gitlab_rule(
        name="standard",
        approvals_required=1,
        users=None,
        groups=None,
        protected_branches=None,
        applies_to_all_protected_branches=False,
        rule_type="regular",
    ):
        return {
            "id": 1,
            "name": name,
            "rule_type": rule_type,
            "report_type": None,
            "eligible_approvers": [],
            "approvals_required": approvals_required,
            "users": users or [],
            "groups": groups or [],
            "contains_hidden_groups": False,
            "protected_branches": protected_branches or [],
            "applies_to_all_protected_branches": applies_to_all_protected_branches,
        }

    def test_no_update_when_users_match(self):
        gitlab_rule = self._gitlab_rule(
            users=[{"id": 5, "username": "alice"}, {"id": 7, "username": "bob"}],
        )
        config = {"name": "standard", "approvals_required": 1, "user_ids": [7, 5]}

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_no_update_when_groups_match(self):
        gitlab_rule = self._gitlab_rule(groups=[{"id": 3, "name": "sec"}])
        config = {"name": "standard", "approvals_required": 1, "group_ids": [3]}

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_no_update_when_protected_branches_match(self):
        gitlab_rule = self._gitlab_rule(
            protected_branches=[
                {"id": 1, "name": "main"},
                {"id": 2, "name": "release"},
            ],
        )
        config = {
            "name": "standard",
            "approvals_required": 1,
            "protected_branches": ["release", "main"],
        }

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_no_update_when_config_omits_user_ids_and_gitlab_has_no_users(self):
        gitlab_rule = self._gitlab_rule()
        config = {"name": "standard", "approvals_required": 1}

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_no_update_when_gitlab_omits_users_groups_protected_branches_keys(self):
        gitlab_rule = {
            "id": 1,
            "name": "standard",
            "rule_type": "regular",
            "approvals_required": 1,
        }
        config = {"name": "standard", "approvals_required": 1}

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_update_when_user_ids_differ(self):
        gitlab_rule = self._gitlab_rule(users=[{"id": 5, "username": "alice"}])
        config = {"name": "standard", "approvals_required": 1, "user_ids": [9]}

        assert self.processor._needs_update(gitlab_rule, config) is True

    def test_update_when_config_clears_users_but_gitlab_has_users(self):
        gitlab_rule = self._gitlab_rule(users=[{"id": 5, "username": "alice"}])
        config = {"name": "standard", "approvals_required": 1}

        assert self.processor._needs_update(gitlab_rule, config) is True

    def test_no_update_when_protected_branch_ids_match(self):
        # the config can also reference branches directly by id
        gitlab_rule = self._gitlab_rule(protected_branches=[{"id": 42, "name": "main"}])
        config = {"name": "standard", "approvals_required": 1, "protected_branch_ids": [42]}

        assert self.processor._needs_update(gitlab_rule, config) is False

    def test_update_when_protected_branch_ids_differ(self):
        gitlab_rule = self._gitlab_rule(protected_branches=[{"id": 42, "name": "main"}])
        config = {"name": "standard", "approvals_required": 1, "protected_branch_ids": [43]}

        assert self.processor._needs_update(gitlab_rule, config) is True

    def test_update_when_protected_branches_differ(self):
        gitlab_rule = self._gitlab_rule(
            protected_branches=[{"id": 1, "name": "main"}],
        )
        config = {
            "name": "standard",
            "approvals_required": 1,
            "protected_branches": ["release"],
        }

        assert self.processor._needs_update(gitlab_rule, config) is True

    def test_update_when_approvals_required_changes(self):
        gitlab_rule = self._gitlab_rule(approvals_required=1)
        config = {"name": "standard", "approvals_required": 2}

        assert self.processor._needs_update(gitlab_rule, config) is True

    def test_no_update_for_any_approver_rule(self):
        gitlab_rule = self._gitlab_rule(rule_type="any_approver", approvals_required=0)
        config = {
            "name": "standard",
            "approvals_required": 0,
            "rule_type": "any_approver",
        }

        assert self.processor._needs_update(gitlab_rule, config) is False
