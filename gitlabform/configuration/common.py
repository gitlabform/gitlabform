from abc import ABC

from gitlabform.configuration.core import ConfigurationCore


class ConfigurationCommon(ConfigurationCore, ABC):
    """
    Gets the common configuration, applied to all groups and projects.
    """

    def get_common_config(self) -> dict:
        """
        :return: literal common configuration or empty dict if not defined
        """
        common_config = self.get("projects_and_groups|*", {})
        if common_config:
            section_name = "*"
            self._validate_break_inheritance_flag(common_config, section_name)
        return common_config
