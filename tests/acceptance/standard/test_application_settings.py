import logging

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
        projects_and_groups:
          placeholder:
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

    def test__can_detect_when_no_changes_required_to_application_settings(
        self, gl, project, caplog
    ):
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
        projects_and_groups:
          placeholder:
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
