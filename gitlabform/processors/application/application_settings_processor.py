from logging import info, debug

from gitlab.v4.objects import ApplicationSettings

from gitlabform import GitLab
from gitlabform.processors import AbstractProcessor


# https://docs.gitlab.com/ee/api/settings.html
class ApplicationSettingsProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab):
        super().__init__("settings", gitlab)

    def _process_configuration(self, project_or_group_name: str, application_configuration: dict):
        application_settings_config = application_configuration["settings"]
        application_settings: ApplicationSettings = self.gl.settings.get()

        if self._needs_update(application_settings.asdict(), application_settings_config):
            info("Updating Application Settings")
            self.update_application_settings(application_settings, application_settings_config)
        else:
            debug("No update needed for Application Settings")

    @staticmethod
    def update_application_settings(application_settings: ApplicationSettings, application_settings_config: dict):
        # application settings has to be like this:
        # {
        #     'setting1': value1,
        #     'setting2': value2,
        # }
        # ..as documented at: https://docs.gitlab.com/ee/api/settings.html#change-application-settings

        for key in application_settings_config:
            value = application_settings_config[key]
            debug(f"Updating setting {key} to value {value}")
            application_settings.__setattr__(key, value)

        application_settings.save()
