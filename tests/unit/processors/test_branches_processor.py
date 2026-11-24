from unittest.mock import MagicMock

import pytest
from gitlab import GitlabGetError

from gitlabform.gitlab import AccessLevel
from gitlabform.processors.project.branches_processor import BranchesProcessor
from gitlabform.processors.util.branch_protection import BranchProtection

def _config_item(**kwargs):
    """A transformed config item, as produced by BranchProtection.map_config_to_protected_branch_get_data"""
    return {"id": None, "access_level": None, "user_id": None, "group_id": None, "deploy_key_id": None, **kwargs}


def _gitlab_record(record_id, **kwargs):
    """An access level record, as returned by GitLab's protected branches GET endpoint"""
    return {"id": record_id, "access_level": None, "user_id": None, "group_id": None, "deploy_key_id": None, **kwargs}

# Since GitLab 19 user/group/deploy key records carry a non-null access_level (e.g. 40 for maintainer),
# earlier versions returned null. See https://github.com/gitlabform/gitlabform/issues/1399
USER_ID = 9518
OTHER_USER_ID = 42
GROUP_ID = 5
DEPLOY_KEY_ID = 7
USER_RECORD = _gitlab_record(41361, user_id=USER_ID, access_level=AccessLevel.MAINTAINER.value)
OTHER_USER_RECORD = _gitlab_record(41362, user_id=OTHER_USER_ID, access_level=AccessLevel.MAINTAINER.value)
GROUP_RECORD = _gitlab_record(41363, group_id=GROUP_ID, access_level=AccessLevel.MAINTAINER.value)
DEPLOY_KEY_RECORD = _gitlab_record(41364, deploy_key_id=DEPLOY_KEY_ID, access_level=AccessLevel.MAINTAINER.value)
NO_ACCESS_RECORD = _gitlab_record(41360, access_level=AccessLevel.NO_ACCESS.value)
MAINTAINER_RECORD = _gitlab_record(41365, access_level=AccessLevel.MAINTAINER.value)


class TestBranchesProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.strict = False
        self.processor = BranchesProcessor(self.gitlab, self.strict)

    def test_is_branch_name_wildcard(self):
        # Test cases with wildcards
        assert BranchesProcessor.branch_name_contains_supported_wildcard("branch*") is True
        assert BranchesProcessor.branch_name_contains_supported_wildcard("*branch") is True
        assert BranchesProcessor.branch_name_contains_supported_wildcard("br*nch") is True

        # Test cases with unsupported wildcards
        assert BranchesProcessor.branch_name_contains_supported_wildcard("branch?") is False
        assert BranchesProcessor.branch_name_contains_supported_wildcard("?branch") is False
        assert BranchesProcessor.branch_name_contains_supported_wildcard("br?nch") is False

        # Test cases without wildcards
        assert BranchesProcessor.branch_name_contains_supported_wildcard("branch") is False
        assert BranchesProcessor.branch_name_contains_supported_wildcard("main") is False
        assert BranchesProcessor.branch_name_contains_supported_wildcard("feature-123") is False

    def test_skip_missing_branch_skips_protection_for_missing_literal_branch_from_global_branches_config(self):
        project = MagicMock()
        project.branches.get.side_effect = GitlabGetError("not found", 404)
        project.protectedbranches.get.side_effect = GitlabGetError("not protected", 404)

        self.processor.gl = MagicMock()
        self.processor.gl.get_project_by_path_cached.return_value = project

        self.processor._process_configuration(
            "group/project",
            {"branches": {"skip_missing_branch": True, "main": {"protected": True}}},
        )

        project.protectedbranches.create.assert_not_called()

    def test_skip_missing_branch_does_not_skip_wildcard_branch_protection(self):
        project = MagicMock()
        project.branches.get.side_effect = GitlabGetError("not found", 404)
        project.protectedbranches.get.side_effect = GitlabGetError("not protected", 404)

        self.processor.gl = MagicMock()
        self.processor.gl.get_project_by_path_cached.return_value = project

        self.processor._process_configuration(
            "group/project",
            {"branches": {"skip_missing_branch": True, "release-*": {"protected": True}}},
        )

        project.protectedbranches.create.assert_called_once()

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
        assert BranchProtection.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is False

        # Test with different access levels
        cfg_in_gitlab = [{"access_level": 30, "user_id": None, "group_id": None}]
        local_cfg = [{"access_level": 40, "user_id": None, "group_id": None}]
        assert BranchProtection.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different user_ids
        cfg_in_gitlab = [{"access_level": None, "user_id": 30, "group_id": None}]
        local_cfg = [{"access_level": None, "user_id": 40, "group_id": None}]
        assert BranchProtection.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different group_ids
        cfg_in_gitlab = [{"access_level": None, "user_id": None, "group_id": 30}]
        local_cfg = [{"access_level": None, "user_id": None, "group_id": 40}]
        assert BranchProtection.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

        # Test with different lengths
        cfg_in_gitlab = [{"access_level": None, "user_id": 40, "group_id": None}]
        local_cfg = [
            {"access_level": None, "user_id": 40, "group_id": None},
            {"access_level": None, "user_id": 30, "group_id": None},
        ]
        assert BranchProtection.naive_access_level_diff_analyzer("test_key", cfg_in_gitlab, local_cfg) is True

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
        result_access_level = BranchProtection.map_config_to_protected_branch_get_data(our_branch_config_access_level)
        result_allowed_to = BranchProtection.map_config_to_protected_branch_get_data(our_branch_config_allowed_to)

        expected_result_access_level = {
            "merge_access_levels": [
                {"id": None, "access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None}
            ],
            "push_access_levels": [
                {"id": None, "access_level": 30, "user_id": None, "group_id": None, "deploy_key_id": None}
            ],
            "unprotect_access_levels": [
                {"id": None, "access_level": 20, "user_id": None, "group_id": None, "deploy_key_id": None}
            ],
        }

        expected_result_allowed_to = {
            "merge_access_levels": [
                {"id": None, "access_level": 50, "user_id": None, "group_id": None, "deploy_key_id": None},
                {"id": None, "access_level": None, "user_id": 123, "group_id": None, "deploy_key_id": None},
            ],
            "push_access_levels": [
                {"id": None, "access_level": None, "user_id": None, "group_id": 456, "deploy_key_id": None}
            ],
            "unprotect_access_levels": [
                {"id": None, "access_level": 60, "user_id": None, "group_id": None, "deploy_key_id": None},
                {"id": None, "access_level": None, "user_id": 789, "group_id": None, "deploy_key_id": None},
            ],
        }

        assert result_access_level == expected_result_access_level
        assert result_allowed_to == expected_result_allowed_to

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

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
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

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
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

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
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

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
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
                    "user_id": 23,
                    "id": 18,
                },
            ]
        )

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
        # Additive Design: Omitted users should be retained, not destroyed.
        assert result == []

    @pytest.mark.parametrize(
        "transformed_access_levels, existing_records",
        [
            pytest.param(
                [_config_item(access_level=AccessLevel.NO_ACCESS.value), _config_item(user_id=USER_ID)],
                (USER_RECORD, NO_ACCESS_RECORD),
                id="no_access_then_user",
            ),
            pytest.param(
                [_config_item(user_id=USER_ID), _config_item(access_level=AccessLevel.NO_ACCESS.value)],
                (USER_RECORD, NO_ACCESS_RECORD),
                id="user_then_no_access",
            ),
            pytest.param(
                [_config_item(access_level=AccessLevel.NO_ACCESS.value), _config_item(user_id=USER_ID)],
                (NO_ACCESS_RECORD, USER_RECORD),
                id="no_access_then_user_gitlab_returns_role_first",
            ),
            pytest.param(
                [_config_item(access_level=AccessLevel.MAINTAINER.value), _config_item(user_id=USER_ID)],
                (USER_RECORD, MAINTAINER_RECORD),
                id="issue_1399_maintainer_then_user",
            ),
            pytest.param(
                [_config_item(access_level=AccessLevel.MAINTAINER.value), _config_item(user_id=USER_ID)],
                (MAINTAINER_RECORD, USER_RECORD),
                id="issue_1399_maintainer_then_user_gitlab_returns_role_first",
            ),
            pytest.param(
                [
                    _config_item(access_level=AccessLevel.MAINTAINER.value),
                    _config_item(user_id=USER_ID),
                    _config_item(user_id=OTHER_USER_ID),
                ],
                (USER_RECORD, OTHER_USER_RECORD, MAINTAINER_RECORD),
                id="issue_1399_maintainer_then_two_users",
            ),
            pytest.param(
                [_config_item(access_level=AccessLevel.NO_ACCESS.value), _config_item(group_id=GROUP_ID)],
                (GROUP_RECORD, NO_ACCESS_RECORD),
                id="no_access_then_group",
            ),
            pytest.param(
                [_config_item(access_level=AccessLevel.NO_ACCESS.value), _config_item(deploy_key_id=DEPLOY_KEY_ID)],
                (DEPLOY_KEY_RECORD, NO_ACCESS_RECORD),
                id="no_access_then_deploy_key",
            ),
        ],
    )
    def test_build_patch_request_data_returns_nothing_when_gitlab_user_group_or_deploy_key_records_have_access_level(
        self, transformed_access_levels, existing_records
    ):
        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == []

    def test_build_patch_request_data_no_access_destroys_existing_role_but_keeps_existing_user(self):
        transformed_access_levels = [
            _config_item(access_level=AccessLevel.NO_ACCESS.value),
            _config_item(user_id=USER_ID),
        ]
        existing_records = (USER_RECORD, MAINTAINER_RECORD)

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [
            {"access_level": AccessLevel.NO_ACCESS.value},
            {"id": MAINTAINER_RECORD["id"], "_destroy": True},
        ]

    def test_build_patch_request_data_role_destroys_existing_no_access_but_keeps_existing_user(self):
        transformed_access_levels = [
            _config_item(access_level=AccessLevel.MAINTAINER.value),
            _config_item(user_id=USER_ID),
        ]
        existing_records = (USER_RECORD, NO_ACCESS_RECORD)

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [
            {"access_level": AccessLevel.MAINTAINER.value},
            {"id": NO_ACCESS_RECORD["id"], "_destroy": True},
        ]

    def test_build_patch_request_data_adds_new_user_alongside_no_access_without_destroying_anything(self):
        transformed_access_levels = [
            _config_item(access_level=AccessLevel.NO_ACCESS.value),
            _config_item(user_id=USER_ID),
            _config_item(user_id=OTHER_USER_ID),
        ]
        existing_records = (USER_RECORD, NO_ACCESS_RECORD)

        result = BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)
        assert result == [{"user_id": OTHER_USER_ID}]

    def _setup_existing_protected_branch(self, push_access_levels, merge_access_levels):
        self.gitlab.is_version_less_than.return_value = False
        self.gitlab.enterprise = True

        protected_branch = MagicMock()
        protected_branch.attributes = {
            "name": "main",
            "push_access_levels": push_access_levels,
            "merge_access_levels": merge_access_levels,
            "unprotect_access_levels": [],
        }

        project = MagicMock()
        project.protectedbranches.get.return_value = protected_branch
        return project

    def test_process_branch_protection_does_not_update_when_config_with_role_and_users_is_unchanged(self):
        project = self._setup_existing_protected_branch(
            push_access_levels=[USER_RECORD, NO_ACCESS_RECORD],
            merge_access_levels=[OTHER_USER_RECORD, MAINTAINER_RECORD],
        )
        branch_config = {
            "protected": True,
            "allowed_to_push": [{"access_level": AccessLevel.NO_ACCESS.value}, {"user_id": USER_ID}],
            "allowed_to_merge": [{"access_level": AccessLevel.MAINTAINER.value}, {"user_id": OTHER_USER_ID}],
        }

        self.processor.process_branch_protection(project, "main", branch_config, False)

        project.protectedbranches.update.assert_not_called()
        project.protectedbranches.create.assert_not_called()
        protected_branch = project.protectedbranches.get.return_value
        protected_branch.delete.assert_not_called()

    def test_process_branch_protection_only_sends_new_user_when_added_to_config_with_role(self):
        project = self._setup_existing_protected_branch(
            push_access_levels=[USER_RECORD, NO_ACCESS_RECORD],
            merge_access_levels=[MAINTAINER_RECORD],
        )
        branch_config = {
            "protected": True,
            "allowed_to_push": [
                {"access_level": AccessLevel.NO_ACCESS.value},
                {"user_id": USER_ID},
                {"user_id": OTHER_USER_ID},
            ],
            "allowed_to_merge": [{"access_level": AccessLevel.MAINTAINER.value}],
        }

        self.processor.process_branch_protection(project, "main", branch_config, False)

        project.protectedbranches.update.assert_called_once_with(
            "main", {"allowed_to_push": [{"user_id": OTHER_USER_ID}]}
        )