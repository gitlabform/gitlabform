from unittest.mock import MagicMock

import pytest
from gitlab import GitlabCreateError, GitlabGetError

from gitlabform.processors.project.tags_processor import TagsProcessor

MAINTAINERS = {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": None}
USER_5 = {"access_level": 40, "user_id": 5, "group_id": None, "deploy_key_id": None}
GROUP_7 = {"access_level": 40, "user_id": None, "group_id": 7, "deploy_key_id": None}
DEPLOY_KEY_9 = {"access_level": 40, "user_id": None, "group_id": None, "deploy_key_id": 9}


class TestTagsProcessor:
    def setup_method(self):
        self.project = MagicMock()
        self.processor = TagsProcessor(MagicMock(), strict=False)
        self.processor.gl = MagicMock()
        self.processor.gl.get_project_by_path_cached.return_value = self.project

    def test_unchanged_rule_is_left_alone(self):
        self.project.protectedtags.get.return_value.create_access_levels = [MAINTAINERS, USER_5]

        self.processor._process_configuration(
            "group/project",
            {"tags": {"v*": {"protected": True, "allowed_to_create": [{"user_id": 5}, {"access_level": 40}]}}},
        )

        self.project.protectedtags.delete.assert_not_called()
        self.project.protectedtags.create.assert_not_called()

    def test_changed_rule_is_recreated(self):
        self.project.protectedtags.get.return_value.create_access_levels = [MAINTAINERS]

        self.processor._process_configuration(
            "group/project",
            {"tags": {"v*": {"protected": True, "allowed_to_create": [{"access_level": 30}, {"user_id": 5}]}}},
        )

        self.project.protectedtags.delete.assert_called_once_with("v*")
        self.project.protectedtags.create.assert_called_once_with(
            {"name": "v*", "create_access_level": 30, "allowed_to_create": [{"user_id": 5}]}
        )

    def test_previous_rule_is_restored_when_create_fails(self):
        self.project.protectedtags.get.return_value.create_access_levels = [MAINTAINERS, USER_5, GROUP_7, DEPLOY_KEY_9]
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

    def test_current_and_desired_state_have_the_same_shape(self):
        protected_tag = MagicMock()
        protected_tag.name = "v*"
        protected_tag.create_access_levels = [USER_5, MAINTAINERS]
        self.project.protectedtags.list.return_value = [protected_tag]

        assert self.processor._get_current_state("group/project") == {
            "v*": {"protected": True, "allowed_to_create": [{"access_level": 40}, {"user_id": 5}]},
        }
        assert self.processor._get_desired_state(
            {
                "v*": {"protected": True, "allowed_to_create": [{"user_id": 5}], "create_access_level": 40},
                "release-*": {"protected": True},
                "old-*": {"protected": False},
            }
        ) == {
            "v*": {"protected": True, "allowed_to_create": [{"access_level": 40}, {"user_id": 5}]},
            "release-*": {"protected": True, "allowed_to_create": [{"access_level": 40}]},
            "old-*": {"protected": False},
        }
