from unittest.mock import MagicMock, patch, call

from gitlabform.processors.project.branches_processor import BranchesProcessor


class TestBranchesProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.strict = False
        self.processor = BranchesProcessor(self.gitlab, self.strict)

    def test_is_branch_name_wildcard(self):
        # Test cases with wildcards
        assert BranchesProcessor.is_branch_name_wildcard("branch*") is True
        assert BranchesProcessor.is_branch_name_wildcard("*branch") is True
        assert BranchesProcessor.is_branch_name_wildcard("br*nch") is True
        assert BranchesProcessor.is_branch_name_wildcard("branch?") is True
        assert BranchesProcessor.is_branch_name_wildcard("?branch") is True
        assert BranchesProcessor.is_branch_name_wildcard("br?nch") is True

        # Test cases without wildcards
        assert BranchesProcessor.is_branch_name_wildcard("branch") is False
        assert BranchesProcessor.is_branch_name_wildcard("main") is False
        assert BranchesProcessor.is_branch_name_wildcard("feature-123") is False

    def test_convert_user_and_group_names_to_ids(self):
        # Setup
        self.processor.gl = MagicMock()
        self.processor.gl.get_user_id_cached.return_value = 123
        self.processor.gl.get_group_id.return_value = 456

        # Test with user
        config_with_user = {"allowed_to_push": [{"user": "johndoe"}], "protected": True}
        result = self.processor.convert_user_and_group_names_to_ids(config_with_user)
        assert result["allowed_to_push"][0]["user_id"] == 123
        assert "user" not in result["allowed_to_push"][0]

        # Test with group
        config_with_group = {"allowed_to_merge": [{"group": "developers"}], "protected": True}
        result = self.processor.convert_user_and_group_names_to_ids(config_with_group)
        assert result["allowed_to_merge"][0]["group_id"] == 456
        assert "group" not in result["allowed_to_merge"][0]

    def test_naive_access_level_diff_analyzer(self):
        # Test with equal configurations
        cfg_in_gitlab = [{"access_level": 40, "user_id": None, "group_id": None}]
        local_cfg = [{"access_level": 40, "user_id": None, "group_id": None}]
        assert BranchesProcessor.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is False

        # Test with different access levels
        cfg_in_gitlab = [{"access_level": 30, "user_id": None, "group_id": None}]
        local_cfg = [{"access_level": 40, "user_id": None, "group_id": None}]
        assert BranchesProcessor.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different user_ids
        cfg_in_gitlab = [{"access_level": None, "user_id": 30, "group_id": None}]
        local_cfg = [{"access_level": None, "user_id": 40, "group_id": None}]
        assert BranchesProcessor.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different group_ids
        cfg_in_gitlab = [{"access_level": None, "user_id": None, "group_id": 30}]
        local_cfg = [{"access_level": None, "user_id": None, "group_id": 40}]
        assert BranchesProcessor.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different lengths
        cfg_in_gitlab = [{"access_level": None, "user_id": 40, "group_id": None}]
        local_cfg = [
            {"access_level": None, "user_id": 40, "group_id": None},
            {"access_level": None, "user_id": 30, "group_id": None},
        ]
        assert BranchesProcessor.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

    def test_transform_branch_config_access_levels(self):
        our_branch_config_access_level = {
            "merge_access_level": 40,
            "push_access_level": 30,
            "unprotect_access_level": 20,
            "protected": True,
        }
        our_branch_config_allowed_to = {
            "allowed_to_merge": [{"access_level": 50}, {"user_id": 123}],
            "allowed_to_push": [{"group_id": 456}],
            "allowed_to_unprotect": [{"access_level": 60}, {"user_id": 789}],
            "protected": True,
        }
        result_access_level = self.processor.transform_branch_config_access_levels(our_branch_config_access_level)
        result_allowed_to = self.processor.transform_branch_config_access_levels(our_branch_config_allowed_to)

        expected_result_access_level = {
            "merge_access_levels": [{"id": None, "access_level": 40, "user_id": None, "group_id": None}],
            "push_access_levels": [{"id": None, "access_level": 30, "user_id": None, "group_id": None}],
            "unprotect_access_levels": [{"id": None, "access_level": 20, "user_id": None, "group_id": None}],
        }

        expected_result_allowed_to = {
            "merge_access_levels": [
                {"id": None, "access_level": 50, "user_id": None, "group_id": None},
                {"id": None, "access_level": None, "user_id": 123, "group_id": None},
            ],
            "push_access_levels": [{"id": None, "access_level": None, "user_id": None, "group_id": 456}],
            "unprotect_access_levels": [
                {"id": None, "access_level": 60, "user_id": None, "group_id": None},
                {"id": None, "access_level": None, "user_id": 789, "group_id": None},
            ],
        }

        assert result_access_level == expected_result_access_level
        assert result_allowed_to == expected_result_allowed_to

    def test_set_allow_force_push_returns_false_when_config_matches_gitlab(self):
        branch_config = {
            "allow_force_push": True,
        }
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.set_allow_force_push(branch_config, protected_branch)
        assert result is False
        assert protected_branch.allow_force_push is True

    def test_set_allow_force_push_returns_true_when_config_differs_from_gitlab(self):
        branch_config = {
            "allow_force_push": False,
        }
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.set_allow_force_push(branch_config, protected_branch)
        assert result is True
        assert protected_branch.allow_force_push is False

    def test_set_allow_force_push_returns_true_when_config_is_not_defined_and_gitlab_is_set_to_true(self):
        branch_config = {}
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.set_allow_force_push(branch_config, protected_branch)
        assert result is True
        assert protected_branch.allow_force_push is False

    def test_set_code_owner_approval_required_returns_false_when_config_matches_gitlab(self):
        branch_config = {
            "code_owner_approval_required": True,
        }
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = True
        result = BranchesProcessor.set_code_owner_approval_required(branch_config, protected_branch)
        assert result is False
        assert protected_branch.code_owner_approval_required is True

    def test_set_code_owner_approval_required_returns_true_when_config_differs_from_gitlab(self):
        branch_config = {
            "code_owner_approval_required": False,
        }
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = True
        result = BranchesProcessor.set_code_owner_approval_required(branch_config, protected_branch)
        assert result is True
        assert protected_branch.code_owner_approval_required is False

    def test_set_code_owner_approval_required_returns_true_when_config_is_not_defined_and_gitlab_is_set_to_true(self):
        branch_config = {}
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = True
        result = BranchesProcessor.set_code_owner_approval_required(branch_config, protected_branch)
        assert result is True
        assert protected_branch.code_owner_approval_required is False
