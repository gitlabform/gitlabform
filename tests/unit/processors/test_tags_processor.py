from unittest.mock import MagicMock

import pytest
from gitlab import GitlabCreateError, GitlabGetError

from gitlabform.processors.project.tags_processor import TagsProcessor


class TestTagsProcessor:
    def setup_method(self):
        self.project = MagicMock()
        self.processor = TagsProcessor(MagicMock(), strict=False)
        self.processor.gl = MagicMock()
        self.processor.gl.get_project_by_path_cached.return_value = self.project

    def test_previous_rule_is_restored_when_create_fails(self):
        self.project.protectedtags.get.return_value.create_access_levels = [
            {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None},
            {"access_level": 40, "user_id": 5, "group_id": None, "deploy_key_id": None},
            {"access_level": 40, "user_id": None, "group_id": 7, "deploy_key_id": None},
            {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": 9},
        ]
        self.project.protectedtags.create.side_effect = [GitlabCreateError("user is not a member", 422), None]

        with pytest.raises(GitlabCreateError):
            self.processor._process_configuration(
                "group/project",
                {"tags": {"v*": {"protected": True, "allowed_to_create": [{"user_id": 6}]}}},
            )

        self.project.protectedtags.create.assert_called_with(
            {
                "name": "v*",
                "create_access_level": 40,
                "allowed_to_create": [{"user_id": 5}, {"group_id": 7}, {"deploy_key_id": 9}],
            }
        )

    def test_original_error_is_raised_when_restore_fails(self):
        self.project.protectedtags.get.return_value.create_access_levels = [
            {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None},
        ]
        self.project.protectedtags.create.side_effect = [
            GitlabCreateError("new rule rejected", 422),
            GitlabCreateError("previous rule rejected", 422),
        ]

        with pytest.raises(GitlabCreateError, match="new rule rejected"):
            self.processor._process_configuration(
                "group/project",
                {"tags": {"v*": {"protected": True, "allowed_to_create": [{"user_id": 6}]}}},
            )

    def test_rule_is_left_alone_when_it_cannot_be_read(self):
        self.project.protectedtags.get.side_effect = GitlabGetError("server error", 500)

        with pytest.raises(GitlabGetError, match="server error"):
            self.processor._process_configuration(
                "group/project",
                {"tags": {"v*": {"protected": True, "allowed_to_create": [{"user_id": 6}]}}},
            )

        self.project.protectedtags.delete.assert_not_called()
        self.project.protectedtags.create.assert_not_called()

    def test_unknown_user_is_skipped_with_a_warning_when_not_strict(self):
        self.processor.gl.get_user_id_cached.return_value = None

        self.processor._process_configuration(
            "group/project",
            {"tags": {"v*": {"protected": True, "allowed_to_create": [{"user": "nobody"}]}}},
        )

        self.project.protectedtags.create.assert_not_called()
