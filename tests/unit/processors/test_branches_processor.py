from unittest.mock import MagicMock

from gitlabform.gitlab import AccessLevel
from gitlabform.processors.project.branches_processor import BranchesProcessor


class TestBranchesProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.strict = False
        self.processor = BranchesProcessor(self.gitlab, self.strict)

    def test_is_branch_name_wildcard(self):
        # Test cases with wildcards
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("branch*") is True
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("*branch") is True
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("br*nch") is True

        # Test cases with unsupported wildcards
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("branch?") is False
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("?branch") is False
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("br?nch") is False

        # Test cases without wildcards
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("branch") is False
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("main") is False
        assert BranchesProcessor.is_branch_name_supported_protected_branch_wildcard("feature-123") is False

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

    def test_get_allow_force_push_data_returns_none_when_config_matches_gitlab(self):
        branch_config = {
            "allow_force_push": True,
        }
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.get_allow_force_push_data(branch_config, protected_branch)
        assert result is None
        assert protected_branch.allow_force_push is True

    def test_get_allow_force_push_data_returns_new_state_without_modifying_branch_when_config_differs_from_gitlab(self):
        branch_config = {
            "allow_force_push": False,
        }
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.get_allow_force_push_data(branch_config, protected_branch)
        assert result is False
        assert protected_branch.allow_force_push is True

    def test_get_allow_force_push_data_returns_false_without_modifying_branch_when_config_is_not_defined_and_gitlab_is_set_to_true(
        self,
    ):
        branch_config = {}
        protected_branch = MagicMock()
        protected_branch.allow_force_push = True
        result = BranchesProcessor.get_allow_force_push_data(branch_config, protected_branch)
        assert result is False
        assert protected_branch.allow_force_push is True

    def test_get_code_owner_approval_required_data_returns_none_when_config_matches_gitlab(self):
        branch_config = {
            "code_owner_approval_required": True,
        }
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = True
        result = BranchesProcessor.get_code_owner_approval_required_data(branch_config, protected_branch)
        assert result is None
        assert protected_branch.code_owner_approval_required is True

    def test_get_code_owner_approval_required_data_returns_true_without_modifying_branch_when_config_differs_from_gitlab(
        self,
    ):
        branch_config = {
            "code_owner_approval_required": True,
        }
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = False
        result = BranchesProcessor.get_code_owner_approval_required_data(branch_config, protected_branch)
        assert result is True
        assert protected_branch.code_owner_approval_required is False

    def test_get_code_owner_approval_required_data_returns_false_without_modifying_branch_when_config_is_not_defined_and_gitlab_is_set_to_true(
        self,
    ):
        branch_config = {}
        protected_branch = MagicMock()
        protected_branch.code_owner_approval_required = True
        result = BranchesProcessor.get_code_owner_approval_required_data(branch_config, protected_branch)
        assert result is False
        assert protected_branch.code_owner_approval_required is True

    def test_build_patch_request_data_returns_nothing_if_no_config_defined_and_gitlab_has_maintainer_access_already(
        self,
    ):
        transformed_access_levels = None
        existing_records = tuple(
            [
                {
                    "access_level": AccessLevel.MAINTAINER.value,
                }
            ]
        )

        result = BranchesProcessor.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == []

    def test_build_patch_request_data_returns_nothing_when_config_access_level_matches_gitlab_access_level(self):
        transformed_access_levels = [
            {
                "access_level": AccessLevel.MAINTAINER.value,
            }
        ]
        existing_records = tuple(
            [
                {
                    "access_level": AccessLevel.MAINTAINER.value,
                }
            ]
        )

        result = BranchesProcessor.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == []

    def test_build_patch_request_data_when_config_has_additional_data_to_gitlab(self):
        transformed_access_levels = [
            {
                "access_level": AccessLevel.MAINTAINER.value,
            },
            {"user_id": 23},
            {
                "group_id": 54,
            },
        ]
        existing_records = tuple([{"access_level": AccessLevel.MAINTAINER.value, "id": 17}])

        result = BranchesProcessor.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [
            {
                "user_id": 23,
            },
            {
                "group_id": 54,
            },
        ]

    def test_build_patch_request_data_when_config_has_different_access_level_to_gitlab(self):
        transformed_access_levels = [
            {
                "access_level": AccessLevel.NO_ACCESS.value,
            }
        ]
        existing_records = tuple([{"access_level": AccessLevel.MAINTAINER.value, "id": 17}])

        result = BranchesProcessor.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [
            {
                "access_level": AccessLevel.NO_ACCESS.value,
            },
            {
                "id": 17,
                "_destroy": True,
            },
        ]

    def test_build_patch_request_data_when_config_is_remove_user_access_to_gitlab(self):
        transformed_access_levels = [
            {
                "access_level": AccessLevel.MAINTAINER.value,
            }
        ]
        existing_records = tuple(
            [
                {"access_level": AccessLevel.MAINTAINER.value, "id": 17},
                {
                    "used_id": 23,
                    "id": 18,
                },
            ]
        )

        result = BranchesProcessor.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [
            {
                "id": 18,
                "_destroy": True,
            },
        ]
