from unittest.mock import MagicMock

import pytest
from gitlab import GitlabGetError, GitlabDeleteError, GitlabOperationError

from gitlabform.processors.group.group_branches_processor import GroupBranchesProcessor


class TestGroupBranchesProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.strict = True
        self.processor = GroupBranchesProcessor(self.gitlab, self.strict)

    def test_can_proceed_valid_config(self):
        configuration = {
            "group_branches": {
                "main": {"protected": True},
            }
        }
        assert self.processor._can_proceed("group", configuration) is True

    def test_can_proceed_missing_protected_key(self):
        configuration = {
            "group_branches": {
                "main": {"push_access_level": 0},
            }
        }
        with pytest.raises(SystemExit):
            self.processor._can_proceed("group", configuration)

    def test_process_configuration_iterates_branches(self):
        self.processor.gl = MagicMock()
        group = MagicMock()
        self.processor.gl.get_group_by_path_cached.return_value = group
        group.protectedbranches.get.side_effect = GitlabGetError("not found", 404)

        configuration = {
            "group_branches": {
                "main": {"protected": True, "push_access_level": 0},
                "develop": {"protected": True, "merge_access_level": 30},
            }
        }

        self.processor._process_configuration("my-group", configuration)

        self.processor.gl.get_group_by_path_cached.assert_called_once_with("my-group")
        assert group.protectedbranches.create.call_count == 2

    def test_process_branch_protection_create_new(self):
        group = MagicMock()
        group.protectedbranches.get.side_effect = GitlabGetError("not found", 404)

        branch_config = {"protected": True, "push_access_level": 0, "merge_access_level": 40}

        self.processor.process_branch_protection(group, "main", branch_config)

        group.protectedbranches.create.assert_called_once()
        call_args = group.protectedbranches.create.call_args[0][0]
        assert call_args["name"] == "main"

    def test_process_branch_protection_update_existing(self):
        protected_branch = MagicMock()
        protected_branch.attributes = {
            "push_access_levels": [
                {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 1}
            ],
            "merge_access_levels": [
                {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 2}
            ],
            "unprotect_access_levels": [],
        }
        protected_branch.allow_force_push = False

        group = MagicMock()
        group.protectedbranches.get.return_value = protected_branch

        branch_config = {
            "protected": True,
            "push_access_level": 0,
            "merge_access_level": 40,
            "allow_force_push": True,
        }

        self.processor.process_branch_protection(group, "main", branch_config)

        group.protectedbranches.update.assert_called_once()
        call_args = group.protectedbranches.update.call_args
        assert call_args[0][0] == "main"
        assert call_args[0][1]["allow_force_push"] is True

    def test_process_branch_protection_update_unprotect_access_level(self):
        protected_branch = MagicMock()
        protected_branch.attributes = {
            "push_access_levels": [
                {"access_level": 0, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 1}
            ],
            "merge_access_levels": [
                {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 2}
            ],
            "unprotect_access_levels": [
                {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 3}
            ],
        }

        group = MagicMock()
        group.protectedbranches.get.return_value = protected_branch

        branch_config = {
            "protected": True,
            "push_access_level": 0,
            "merge_access_level": 40,
            "unprotect_access_level": 30,
        }

        self.processor.process_branch_protection(group, "main", branch_config)

        group.protectedbranches.update.assert_called_once()
        call_args = group.protectedbranches.update.call_args
        assert "allowed_to_unprotect" in call_args[0][1]

    def test_process_branch_protection_no_update_when_config_matches(self):
        protected_branch = MagicMock()
        protected_branch.attributes = {
            "push_access_levels": [
                {"access_level": 0, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 1}
            ],
            "merge_access_levels": [
                {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None, "id": 2}
            ],
            "unprotect_access_levels": [],
        }
        protected_branch.allow_force_push = False

        group = MagicMock()
        group.protectedbranches.get.return_value = protected_branch

        branch_config = {
            "protected": True,
            "push_access_level": 0,
            "merge_access_level": 40,
        }

        self.processor.process_branch_protection(group, "main", branch_config)

        group.protectedbranches.update.assert_not_called()
        group.protectedbranches.create.assert_not_called()

    def test_process_branch_protection_unprotect(self):
        protected_branch = MagicMock()
        group = MagicMock()
        group.protectedbranches.get.return_value = protected_branch

        self.processor.process_branch_protection(group, "main", {"protected": False})

        protected_branch.delete.assert_called_once()

    def test_process_branch_protection_no_action_when_not_protected_and_not_existing(self):
        group = MagicMock()
        group.protectedbranches.get.side_effect = GitlabGetError("not found", 404)

        self.processor.process_branch_protection(group, "main", {"protected": False})

        group.protectedbranches.create.assert_not_called()
        group.protectedbranches.update.assert_not_called()

    def test_protect_branch_create(self):
        group = MagicMock()

        self.processor.protect_branch(group, "main", {"push_access_level": 0}, False)

        group.protectedbranches.create.assert_called_once_with({"name": "main", "push_access_level": 0})

    def test_protect_branch_update(self):
        group = MagicMock()

        self.processor.protect_branch(group, "main", {"push_access_level": 0}, True)

        group.protectedbranches.update.assert_called_once_with("main", {"push_access_level": 0})

    def test_protect_branch_error_strict_mode(self):
        group = MagicMock()
        group.protectedbranches.create.side_effect = GitlabOperationError("error", 400)

        with pytest.raises(SystemExit):
            self.processor.protect_branch(group, "main", {"push_access_level": 0}, False)

    def test_protect_branch_error_non_strict_mode(self):
        self.processor.strict = False
        group = MagicMock()
        group.protectedbranches.create.side_effect = GitlabOperationError("error", 400)

        self.processor.protect_branch(group, "main", {"push_access_level": 0}, False)

    def test_unprotect_branch(self):
        protected_branch = MagicMock()

        self.processor.unprotect_branch(protected_branch)

        protected_branch.delete.assert_called_once()

    def test_unprotect_branch_error_strict_mode(self):
        protected_branch = MagicMock()
        protected_branch.delete.side_effect = GitlabDeleteError("error", 400)

        with pytest.raises(SystemExit):
            self.processor.unprotect_branch(protected_branch)

    def test_unprotect_branch_error_non_strict_mode(self):
        self.processor.strict = False
        protected_branch = MagicMock()
        protected_branch.delete.side_effect = GitlabDeleteError("error", 400)

        self.processor.unprotect_branch(protected_branch)

    def test_get_list_attribute_returns_value(self):
        protected_branch = MagicMock()
        protected_branch.attributes = {"merge_access_levels": [{"access_level": 40}]}

        result = GroupBranchesProcessor._get_list_attribute(protected_branch, "merge_access_levels")

        assert result == [{"access_level": 40}]

    def test_get_list_attribute_returns_empty_list_when_missing(self):
        protected_branch = MagicMock()
        protected_branch.attributes = {}

        result = GroupBranchesProcessor._get_list_attribute(protected_branch, "merge_access_levels")

        assert result == []
