import logging
import sys

import cli_ui

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.configuration.core import ConfigurationCore

logger = logging.getLogger(__name__)


class ConfigurationGroups(ConfigurationCore):
    def __init__(self, config_path=None, config_string=None):
        super().__init__(config_path, config_string)

    def get_groups(self) -> list:
        """
        :return: sorted list of groups that are EXPLICITLY defined in the config
        """
        groups = []
        projects_and_groups = self.get("projects_and_groups")
        for element in projects_and_groups.keys():
            if element.endswith("/*"):
                # cut off that "/*"
                group_name = element[:-2]
                groups.append(group_name)
        return sorted(groups)

    def get_effective_config_for_group(self, group) -> dict:
        """
        :param group: "group_name"
        :return: merged configuration for this group, from common, group. Merging is additive.
        """

        common_config = self.get_common_config()
        logging.debug("Common config: %s" % common_config)

        group_config = self.get_group_config(group)
        logging.debug("Group config: %s" % group_config)

        if not group_config and not common_config:
            return {}

        return self.merge_configs(common_config, group_config)

    def get_effective_subgroup_config(self, subgroup):

        #
        # Goes through a subgroups hierarchy, from top to bottom
        #
        # "x/y/x" -> ["x", "x/y", "x/y/z"]
        #
        # ...and for each element after 1st generate effective config from previous effective one merged with current:
        #
        #              |     v       |
        #              \---> a       |
        #                    |       v
        #                    \------>b = effective config to return
        #
        # ..where a = merged_config("x", "x/y") and b = merged_config(a, "x/y/z")
        #

        effective_config = {}
        elements = subgroup.split("/")
        last_element = None
        for element in elements:
            if not last_element:
                effective_config = self.get_group_config(element)
                logging.debug(
                    "First level config for '%s': %s" % (element, effective_config)
                )
                last_element = element
            else:
                next_level_subgroup = last_element + "/" + element
                next_level_subgroup_config = self.get_group_config(next_level_subgroup)
                logging.debug(
                    "Config for '%s': %s"
                    % (next_level_subgroup, next_level_subgroup_config)
                )
                effective_config = self.merge_configs(
                    effective_config, next_level_subgroup_config
                )
                logging.debug(
                    "Merged previous level config for '%s' with config for '%s': %s"
                    % (last_element, next_level_subgroup, effective_config)
                )
                last_element = last_element + "/" + element

        return effective_config


class EmptyConfigException(Exception):
    pass
