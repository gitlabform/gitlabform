import functools
from logging import debug

from gitlabform.configuration.core import ConfigurationCore
from gitlabform.ui import to_str


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

    @functools.lru_cache()
    def get_effective_config_for_group(self, group) -> dict:
        """
        :param group: "group_name"
        :return: merged configuration for this group, from common, group. Merging is additive.
        """

        common_config = self.get_common_config()
        debug("Common config: %s", to_str(common_config))

        group_config = self.get_group_config(group)
        debug("Group config: %s", to_str(group_config))

        if not group_config and not common_config:
            return {}

        if common_config:
            self.validate_break_inheritance_flag(
                common_config, level="common", parent=""
            )
        elif not common_config and group_config:
            self.validate_break_inheritance_flag(
                group_config, level="group", parent="empty"
            )

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
                debug(
                    "First level config for '%s': %s", element, to_str(effective_config)
                )
                last_element = element
            else:
                next_level_subgroup = last_element + "/" + element
                next_level_subgroup_config = self.get_group_config(next_level_subgroup)
                debug(
                    "Config for '%s': %s",
                    next_level_subgroup,
                    to_str(next_level_subgroup_config),
                )

                if effective_config:
                    self.validate_break_inheritance_flag(
                        effective_config, level="group", parent=""
                    )
                elif not effective_config and next_level_subgroup_config:
                    self.validate_break_inheritance_flag(
                        next_level_subgroup_config, level="subgroup", parent="empty"
                    )

                effective_config = self.merge_configs(
                    effective_config,
                    next_level_subgroup_config,
                )
                debug(
                    "Merged previous level config for '%s' with config for '%s': %s",
                    last_element,
                    next_level_subgroup,
                    to_str(effective_config),
                )
                last_element = last_element + "/" + element

        return effective_config


class EmptyConfigException(Exception):
    pass
