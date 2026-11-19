import logging

import pytest

from gitlabform.constants import EXIT_INVALID_INPUT
from tests.acceptance import run_gitlabform


class TestApplicationSettings:
    def test__can_set_2fa_application_settings(self, gl, project):
        initial_settings = gl.settings.get()
        assert initial_settings is not None
        assert initial_settings.require_two_factor_authentication is False

        config_app_settings = f"""
        application:
          settings:
            require_two_factor_authentication: true
            two_factor_grace_period: 2
        """

        run_gitlabform(config_app_settings, project)

        updated_settings = gl.settings.get()
        assert updated_settings is not None
        assert updated_settings.require_two_factor_authentication is True
        assert updated_settings.two_factor_grace_period == 2

        # Tear down
        updated_settings.require_two_factor_authentication = False
        updated_settings.two_factor_grace_period = 0
        updated_settings.save()

    def test__can_set_asset_proxy_allowlist_array_field_into_application_settings(self, gl, project):
        initial_settings = gl.settings.get()
        assert initial_settings is not None
        assert initial_settings.asset_proxy_allowlist is not None

        config_app_settings = f"""
          application:
            settings:
              asset_proxy_allowlist: ["example.com", "*.example.com", "your-instance.com"]
          """

        run_gitlabform(config_app_settings, project)

        updated_settings = gl.settings.get()
        assert updated_settings is not None
        assert updated_settings.asset_proxy_allowlist == [
            "example.com",
            "*.example.com",
            "your-instance.com",
            "localhost",
        ]

        # Tear down
        updated_settings.asset_proxy_allowlist = initial_settings.asset_proxy_allowlist
        updated_settings.save()

    def test__can_detect_when_no_changes_required_to_application_settings(self, gl, project, caplog):
        caplog.set_level(logging.DEBUG)
        initial_settings = gl.settings.get()

        initial_settings.require_two_factor_authentication = True
        initial_settings.two_factor_grace_period = 2
        initial_settings.save()

        config_app_settings = f"""
        application:
          settings:
            require_two_factor_authentication: true
            two_factor_grace_period: 2
        """

        run_gitlabform(config_app_settings, project)

        updated_settings = gl.settings.get()
        assert updated_settings is not None
        assert updated_settings.require_two_factor_authentication is True
        assert updated_settings.two_factor_grace_period == 2

        # Check we printed out "No update" as a proxy for checking no api calls made via python-gitlab
        assert "No update needed for Application Settings" in caplog.text

        # Tear down
        updated_settings.require_two_factor_authentication = False
        updated_settings.two_factor_grace_period = 0
        updated_settings.save()

    def test__can_set_application_settings_with_only_application_config(self, gl):
        initial_settings = gl.settings.get()
        assert initial_settings is not None
        assert initial_settings.require_two_factor_authentication is False
        original_require_two_factor_authentication = initial_settings.require_two_factor_authentication
        original_two_factor_grace_period = initial_settings.two_factor_grace_period

        config_app_settings = """
        application:
          settings:
            require_two_factor_authentication: true
            two_factor_grace_period: 2
        """

        try:
            run_gitlabform(config_app_settings, "ALL_DEFINED")

            updated_settings = gl.settings.get()
            assert updated_settings is not None
            assert updated_settings.require_two_factor_authentication is True
            assert updated_settings.two_factor_grace_period == 2
        finally:
            settings = gl.settings.get()
            settings.require_two_factor_authentication = original_require_two_factor_authentication
            settings.two_factor_grace_period = original_two_factor_grace_period
            settings.save()

    def test__fails_without_application_and_projects_and_groups(self, gl):
        config_without_anything_to_do = """
        skip_groups: []
        """

        with pytest.raises(SystemExit) as e:
            run_gitlabform(config_without_anything_to_do, "ALL_DEFINED")
        assert e.value.code == EXIT_INVALID_INPUT
