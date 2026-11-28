from unittest.mock import MagicMock, patch

from gitlabform.configuration import Configuration
from gitlabform.processors.group import GroupProcessors
from gitlabform.processors.group.group_protected_environments_processor import (
    GroupProtectedEnvironmentsProcessor,
)

MAINTAINER_ACCESS = [{"access_level": 40}]
DEVELOPER_ACCESS = [{"access_level": 30}]


class TestGroupProtectedEnvironmentsProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = GroupProtectedEnvironmentsProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    @staticmethod
    def _env(
        name: str = "production",
        deploy_access_levels: list = MAINTAINER_ACCESS,
        required_approval_count: int = 0,
        approval_rules: list | None = None,
    ) -> dict:
        return {
            "name": name,
            "deploy_access_levels": deploy_access_levels,
            "required_approval_count": required_approval_count,
            "approval_rules": approval_rules or [],
        }

    def _group(self, *envs: dict, group_id: int = 123) -> MagicMock:
        group = MagicMock()
        group.id = group_id
        self.gl.get_group_by_path_cached.return_value = group
        self.gl.http_list.return_value = list(envs)
        return group

    def _process(self, group_protected_environments: dict, group_path: str = "test-group") -> None:
        self.processor._process_configuration(
            group_path,
            {"group_protected_environments": group_protected_environments},
        )

    # --------------------------------------------------------- registration

    def test_registered_in_group_processors_after_group_members(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            group_processors = GroupProcessors(MagicMock(), MagicMock(Configuration), strict=True)
        names = group_processors.get_configuration_names()

        assert "group_protected_environments" in names
        assert names.index("group_members") < names.index("group_protected_environments")

    # ------------------------------------------------------------------ add

    def test_creates_environment_when_missing(self):
        self._group(group_id=42)
        env_config = {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}

        self._process({"production": env_config})

        self.gl.http_list.assert_called_once_with("/groups/42/protected_environments", get_all=True)
        self.gl.http_post.assert_called_once_with("/groups/42/protected_environments", post_data=env_config)
        self.gl.http_delete.assert_not_called()

    def test_works_for_subgroup_path(self):
        self._group(group_id=99)
        env_config = {"name": "staging", "deploy_access_levels": DEVELOPER_ACCESS}

        self._process({"staging": env_config}, group_path="parent-group/sub-group")

        self.gl.get_group_by_path_cached.assert_called_once_with("parent-group/sub-group")
        self.gl.http_post.assert_called_once_with("/groups/99/protected_environments", post_data=env_config)

    # --------------------------------------------------------------- update

    def test_recreates_environment_when_access_levels_changed(self):
        existing = self._env("production", MAINTAINER_ACCESS)
        self._group(existing, group_id=42)
        env_config = {"name": "production", "deploy_access_levels": DEVELOPER_ACCESS}

        self._process({"production": env_config})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/production")
        self.gl.http_post.assert_called_once_with("/groups/42/protected_environments", post_data=env_config)

    def test_recreates_environment_when_access_rule_switches_from_role_to_group(self):
        existing = self._env(
            "production",
            [{"id": 1, "access_level": 40, "user_id": None, "group_id": None, "group_inheritance_type": 0}],
        )
        self._group(existing, group_id=42)
        env_config = {"name": "production", "deploy_access_levels": [{"group_id": 77}]}

        self._process({"production": env_config})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/production")
        self.gl.http_post.assert_called_once_with("/groups/42/protected_environments", post_data=env_config)

    def test_recreates_environment_when_required_approval_count_changed(self):
        existing = self._env("production", MAINTAINER_ACCESS, required_approval_count=0)
        self._group(existing, group_id=42)
        env_config = {
            "name": "production",
            "deploy_access_levels": MAINTAINER_ACCESS,
            "required_approval_count": 2,
        }

        self._process({"production": env_config})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/production")
        self.gl.http_post.assert_called_once_with("/groups/42/protected_environments", post_data=env_config)

    def test_recreates_environment_when_approval_rules_changed(self):
        existing = self._env(
            "production",
            MAINTAINER_ACCESS,
            approval_rules=[{"id": 10, "group_id": 55, "required_approvals": 1, "access_level": None, "user_id": None}],
        )
        self._group(existing, group_id=42)
        env_config = {
            "name": "production",
            "deploy_access_levels": MAINTAINER_ACCESS,
            "approval_rules": [{"group_id": 55, "required_approvals": 2}],
        }

        self._process({"production": env_config})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/production")
        self.gl.http_post.assert_called_once_with("/groups/42/protected_environments", post_data=env_config)

    def test_no_churn_when_configured_environment_matches_existing(self):
        existing = self._env(
            "production",
            [
                {
                    "id": 1,
                    "access_level": 40,
                    "access_level_description": "Maintainers",
                    "user_id": None,
                    "group_id": None,
                }
            ],
            required_approval_count=1,
            approval_rules=[
                {
                    "id": 10,
                    "group_id": 55,
                    "required_approvals": 1,
                    "access_level": None,
                    "user_id": None,
                    "group_inheritance_type": 0,
                }
            ],
        )
        self._group(existing, group_id=42)

        self._process(
            {
                "production": {
                    "name": "production",
                    "deploy_access_levels": MAINTAINER_ACCESS,
                    "required_approval_count": 1,
                    "approval_rules": [{"group_id": 55, "required_approvals": 1}],
                }
            }
        )

        self.gl.http_delete.assert_not_called()
        self.gl.http_post.assert_not_called()

    def test_delete_false_is_ignored_and_not_sent_to_the_api(self):
        existing = self._env("production", MAINTAINER_ACCESS)
        self._group(existing, group_id=42)

        self._process(
            {
                "production": {
                    "name": "production",
                    "deploy_access_levels": MAINTAINER_ACCESS,
                    "delete": False,
                }
            }
        )

        self.gl.http_delete.assert_not_called()
        self.gl.http_post.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_environment(self):
        existing = self._env("production")
        self._group(existing, group_id=42)

        self._process({"production": {"name": "production", "delete": True}})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/production")
        self.gl.http_post.assert_not_called()

    def test_delete_true_on_non_existent_is_logged_and_skipped(self, caplog):
        self._group(group_id=42)

        with caplog.at_level("INFO"):
            self._process({"production": {"name": "production", "delete": True}})

        matching = [r for r in caplog.records if "Not deleting production of group_protected_environments" in r.message]
        assert len(matching) == 1
        self.gl.http_delete.assert_not_called()
        self.gl.http_post.assert_not_called()

    def test_delete_url_encodes_environment_name(self):
        existing = self._env("prod/eu")
        self._group(existing, group_id=42)

        self._process({"prod_eu": {"name": "prod/eu", "delete": True}})

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/prod%2Feu")

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_environments(self):
        managed = self._env("production", MAINTAINER_ACCESS)
        stray = self._env("staging")
        self._group(managed, stray, group_id=42)

        self._process(
            {
                "enforce": True,
                "production": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS},
            }
        )

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/staging")
        self.gl.http_post.assert_not_called()

    def test_without_enforce_unmanaged_environments_are_left_alone(self):
        stray = self._env("staging")
        self._group(stray, group_id=42)

        self._process({})

        self.gl.http_delete.assert_not_called()
        self.gl.http_post.assert_not_called()

    def test_enforce_is_not_removed_from_the_shared_configuration(self):
        stray = self._env("staging")
        self._group(stray, group_id=42)
        configuration = {"group_protected_environments": {"enforce": True}}

        self.processor._process_configuration("test-group", configuration)

        self.gl.http_delete.assert_called_once_with("/groups/42/protected_environments/staging")
        assert configuration["group_protected_environments"] == {"enforce": True}
