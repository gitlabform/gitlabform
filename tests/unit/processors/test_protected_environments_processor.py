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

    def test_delete_false_is_ignored_and_not_sent_to_the_api(self):
        # "delete" is a gitlabform control key: an explicit "delete: false" must not
        # trigger a recreate on every run, nor end up in the API payload
        existing = self._env("production", MAINTAINER_ACCESS)
        project = self._project(existing)

        self._process({"prod": {"name": "production", "deploy_access_levels": MAINTAINER_ACCESS, "delete": False}})

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

    def test_enforce_is_not_removed_from_the_shared_configuration(self):
        # the configuration dict is reused when processing is retried, so a run must not mutate it
        stray = self._env("staging")
        self._project(stray)
        configuration = {"protected_environments": {"enforce": True}}

        self.processor._process_configuration("test/project", configuration)

        stray.delete.assert_called_once()
        assert configuration["protected_environments"] == {"enforce": True}
