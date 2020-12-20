import logging
from typing import List

from gitlabform.common.safe_dict import SafeDict
from gitlabform.configuration.core import ConfigurationCore


class ConfigurationChain:
    def __init__(self, projects_and_groups: List[dict]):
        self.config_items = list(map(ConfigurationItem, projects_and_groups))

    def get_effective_config(self, project) -> SafeDict:
        # TODO Implement
        pass


class ConfigurationItem(ConfigurationCore):
    def __init__(self, config_data: dict, key_path_separator: str = "|"):
        super(ConfigurationItem, self).__init__()

        project_path = config_data.get("path")
        if project_path is None:
            logging.error(
                "Each configuration entry must have 'path' property defined.\n"
                "Configuration part with missing 'path' property: %s",
                config_data,
            )
            raise MissingProjectPathException

        self.project_path = ProjectPath(config_data.get("path"))
        self.config_data = SafeDict(
            config_data, key_path_separator=key_path_separator, exclude_keys=["path"]
        )

    def merge(self, other_config):
        """
        :return: merge this config with another one.
                 The other config values take precedence over the current ones.
        """
        merged_config = {}

        for key in other_config.keys() | self.config_data.keys():

            if key in self.config_data and key not in other_config:
                merged_config[key] = self.config_data[key]
            elif key in other_config and key not in self.config_data:
                merged_config[key] = other_config[key]
            else:
                # overwrite more general config settings with more specific config
                merged_config[key] = {
                    **self.config_data[key],
                    **other_config[key],
                }

        return ConfigurationItem(merged_config, self.config_data.key_path_separator)


class MissingProjectPathException(Exception):
    pass
