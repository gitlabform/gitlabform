from unittest.mock import MagicMock, patch

from gitlabform.processors.project.protected_environments_processor import ProtectedEnvironmentsProcessor

MAINTAINER_ACCESS = [{"access_level": 40}]
DEVELOPER_ACCESS = [{"access_level": 30}]


class TestProtectedEnvironmentsProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = ProtectedEnvironmentsProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    @staticmethod
    def _env(name: str = "production", deploy_access_levels: list = MAINTAINER_ACCESS) -> MagicMock:
        env = MagicMock()
        env.name = name
        env.deploy_access_levels = deploy_access_levels
        env.asdict.return_value = {"name": name, "deploy_access_levels": deploy_access_levels}
        return env

    def _project(self, *envs: MagicMock) -> MagicMock:
        project = MagicMock()
        project.protected_environments.list.return_value = list(envs)
        # by default GitLab returns the environment as it was sent
        project.protected_environments.create.side_effect = lambda config: self._env(
            config["name"], config.get("deploy_access_levels", [])
        )
        self.gl.get_project_by_path_cached.return_value = project
        return project

    def _process(self, protected_environments: dict) -> None:
        self.processor._process_configuration("test/project", {"protected_environments": protected_environments})

    # ------------------------------------------------------------------ add

    def test_creates_environment_when_missing(self):
        project = self._project()
        env_config = {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}

        self._process({"prod": env_config})

        project.protected_environments.create.assert_called_once_with(env_config)

    # --------------------------------------------------------------- update

    def test_recreates_environment_when_access_levels_changed(self):
        existing = self._env("production", MAINTAINER_ACCESS)
        project = self._project(existing)
        env_config = {"name": "production", "deploy_access_levels": DEVELOPER_ACCESS}

        self._process({"prod": env_config})

        # python-gitlab doesn't support updating a protected environment, so it is deleted and added again
        existing.delete.assert_called_once()
        project.protected_environments.create.assert_called_once_with(env_config)

    def test_no_churn_when_configured_environment_matches_existing(self):
        existing = self._env("production", MAINTAINER_ACCESS)
        project = self._project(existing)

        self._process({"prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}})

        existing.delete.assert_not_called()
        project.protected_environments.create.assert_not_called()

    def test_no_churn_when_gitlab_adds_extra_access_level_keys(self):
        # GitLab returns keys the config doesn't set (id, user_id, group_id) with None values
        existing = self._env("production", [{"access_level": 40, "user_id": None, "group_id": None}])
        project = self._project(existing)

        self._process({"prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}})

        existing.delete.assert_not_called()
        project.protected_environments.create.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_environment(self):
        existing = self._env("production")
        project = self._project(existing)

        self._process({"prod": {"name": "production", "delete": True}})

        existing.delete.assert_called_once()
        project.protected_environments.create.assert_not_called()

    def test_delete_true_on_non_existent_is_logged_and_skipped(self, caplog):
        project = self._project()

        with caplog.at_level("INFO"):
            self._process({"prod": {"name": "production", "delete": True}})

        matching = [r for r in caplog.records if "Not deleting prod of protected_environments" in r.message]
        assert len(matching) == 1
        project.protected_environments.create.assert_not_called()

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_environments(self):
        managed = self._env("production", MAINTAINER_ACCESS)
        stray = self._env("staging")
        self._project(managed, stray)

        self._process(
            {
                "enforce": True,
                "prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS},
            }
        )

        stray.delete.assert_called_once()
        managed.delete.assert_not_called()

    def test_without_enforce_unmanaged_environments_are_left_alone(self):
        stray = self._env("staging")
        self._project(stray)

        self._process({})

        stray.delete.assert_not_called()

    # -------------------------------------------------- create retry (gitlab#378657)

    def test_create_retries_once_when_access_levels_are_dropped(self):
        # GitLab sometimes applies fewer deploy_access_levels than were sent
        project = self._project()
        incomplete = self._env("production", [])
        complete = self._env("production", MAINTAINER_ACCESS)
        project.protected_environments.create.side_effect = [incomplete, complete]

        self._process({"prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}})

        assert project.protected_environments.create.call_count == 2
        incomplete.delete.assert_called_once()
        complete.delete.assert_not_called()

    def test_create_does_not_retry_more_than_once(self):
        project = self._project()
        incomplete_1 = self._env("production", [])
        incomplete_2 = self._env("production", [])
        project.protected_environments.create.side_effect = [incomplete_1, incomplete_2]

        self._process({"prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS}})

        assert project.protected_environments.create.call_count == 2
        incomplete_2.delete.assert_not_called()
