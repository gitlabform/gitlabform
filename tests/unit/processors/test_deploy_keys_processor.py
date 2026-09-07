from unittest.mock import MagicMock, patch

import pytest
from gitlab.exceptions import GitlabCreateError

from gitlabform.processors.project.deploy_keys_processor import DeployKeysProcessor

PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAA some comment"
OTHER_PUBLIC_KEY = "ssh-rsa BBBBB3NzaC1yc2EAAAA some comment"


class TestDeployKeysProcessor:
    def setup_method(self):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = DeployKeysProcessor(MagicMock())
        self.gl = MagicMock()
        self.processor.gl = self.gl

    @staticmethod
    def _key(title: str, key: str = PUBLIC_KEY, **fields) -> MagicMock:
        deploy_key = MagicMock()
        deploy_key.title = title
        deploy_key.key = key
        for name, value in fields.items():
            setattr(deploy_key, name, value)
        deploy_key.asdict.return_value = {"id": 1, "title": title, "key": key, **fields}
        return deploy_key

    def _project(self, *keys: MagicMock) -> MagicMock:
        project = MagicMock()
        project.keys.list.return_value = list(keys)
        self.gl.get_project_by_path_cached.return_value = project
        return project

    def _process(self, deploy_keys: dict) -> None:
        self.processor._process_configuration("test/project", {"deploy_keys": deploy_keys})

    # ------------------------------------------------------------------ add

    def test_creates_key_when_missing(self):
        project = self._project()
        key_config = {"title": "some_key", "key": PUBLIC_KEY, "can_push": False}

        self._process({"foobar": key_config})

        project.keys.create.assert_called_once_with(key_config)

    # --------------------------------------------------------------- update

    def test_recreates_key_when_value_changed(self):
        existing = self._key("a_key")
        project = self._project(existing)

        self._process({"foobar": {"title": "a_key", "key": OTHER_PUBLIC_KEY}})

        # the API cannot update a key's value, so it is deleted and added again
        existing.delete.assert_called_once()
        project.keys.create.assert_called_once_with({"title": "a_key", "key": OTHER_PUBLIC_KEY})

    def test_no_churn_when_configured_key_matches_existing(self):
        existing = self._key("a_key")
        project = self._project(existing)

        self._process({"foobar": {"title": "a_key", "key": PUBLIC_KEY}})

        existing.delete.assert_not_called()
        project.keys.create.assert_not_called()

    # --------------------------------------------------------------- delete

    def test_delete_true_removes_matching_key(self):
        existing = self._key("some_key")
        project = self._project(existing)

        self._process({"foobar": {"title": "some_key", "delete": True}})

        existing.delete.assert_called_once()
        project.keys.create.assert_not_called()

    def test_delete_true_on_non_existent_is_noop(self):
        project = self._project()

        self._process({"foobar": {"title": "some_key", "delete": True}})

        project.keys.create.assert_not_called()

    def test_delete_is_processed_before_add_regardless_of_config_order(self):
        # re-adding the same key under another title only works once the old title is gone
        stale = self._key("title_before")
        project = self._project(stale)
        call_order = []
        stale.delete.side_effect = lambda *_: call_order.append("delete")
        project.keys.create.side_effect = lambda *_: call_order.append("create")

        self._process(
            {
                "bar": {"title": "title_after", "key": PUBLIC_KEY},
                "foo": {"title": "title_before", "delete": True},
            }
        )

        assert call_order == ["delete", "create"]

    # -------------------------------------------------------------- enforce

    def test_enforce_deletes_unmanaged_keys(self):
        managed = self._key("a_key")
        stray = self._key("stray", key=OTHER_PUBLIC_KEY)
        self._project(managed, stray)

        self._process(
            {
                "enforce": True,
                "foobar": {"title": "a_key", "key": PUBLIC_KEY},
            }
        )

        stray.delete.assert_called_once()
        managed.delete.assert_not_called()

    def test_enforce_deletes_before_adding(self):
        # a key's value is unique within the instance, so the stale title has to go first
        stale = self._key("title_before")
        project = self._project(stale)
        call_order = []
        stale.delete.side_effect = lambda *_: call_order.append("delete")
        project.keys.create.side_effect = lambda *_: call_order.append("create")

        self._process(
            {
                "enforce": True,
                "foobar": {"title": "title_after", "key": PUBLIC_KEY},
            }
        )

        assert call_order == ["delete", "create"]

    def test_without_enforce_unmanaged_keys_are_left_alone(self):
        stray = self._key("stray")
        self._project(stray)

        self._process({})

        stray.delete.assert_not_called()

    # ---------------------------------------------- already taken workaround

    def test_key_taken_elsewhere_is_enabled_for_this_project(self):
        project = self._project()
        project.keys.create.side_effect = GitlabCreateError(
            '400: {"deploy_key.fingerprint_sha256":["has already been taken"]}',
            response_code=400,
        )
        # GitLab truncates the comment of keys returned by the instance-wide endpoint
        instance_key = MagicMock(id=42, key="ssh-rsa AAAAB3NzaC1yc2EAAAA some")
        self.gl.deploykeys.list.return_value = [instance_key]

        self._process({"foobar": {"title": "some_key", "key": PUBLIC_KEY}})

        project.keys.enable.assert_called_once_with(42)

    def test_key_taken_but_not_found_on_instance_reraises(self):
        project = self._project()
        project.keys.create.side_effect = GitlabCreateError(
            '400: {"deploy_key.fingerprint_sha256":["has already been taken"]}',
            response_code=400,
        )
        self.gl.deploykeys.list.return_value = []

        with pytest.raises(GitlabCreateError):
            self._process({"foobar": {"title": "some_key", "key": PUBLIC_KEY}})

        project.keys.enable.assert_not_called()

    def test_other_create_error_is_reraised(self):
        project = self._project()
        project.keys.create.side_effect = GitlabCreateError("400: key is invalid", response_code=400)

        with pytest.raises(GitlabCreateError):
            self._process({"foobar": {"title": "some_key", "key": PUBLIC_KEY}})

        self.gl.deploykeys.list.assert_not_called()

    # ---------------------------------------------------------------- errors

    def test_missing_title_raises(self):
        project = self._project()

        with pytest.raises(KeyError):
            self._process({"foobar": {"key": PUBLIC_KEY}})

        project.keys.create.assert_not_called()
