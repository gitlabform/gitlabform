from abc import ABC

import functools
from logging import debug

from gitlabform.configuration import ConfigurationCommon
from gitlabform.util import to_str


class ConfigurationGroups(ConfigurationCommon, ABC):
    """
    Gets the groups, skipped groups and their effective configuration.

    ConfigurationCommon is an ancestor of this class because the effective group configuration
    depends on the common configuration.
    """

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

    def is_group_skipped(self, group):
        """
        :return: if group is defined in the key with groups to skip,
                 ignoring the case
        """
        return self._is_skipped_case_insensitively(self.get("skip_groups", []), group)

    @functools.lru_cache()
    def get_effective_config_for_group(self, group) -> dict:
        """
        :param group: "group_name"
        :return: merged configuration for this group, from common, group. Merging is additive.
        """

        common_config = self.get_common_config()
        debug("*Effective* common config: %s", to_str(common_config))

        if "/" in group:
            group_config = self._get_effective_subgroup_config(group)
        else:
            group_config = self._get_group_config(group)
        debug("*Effective* group/subgroup config: %s", to_str(group_config))

        if not common_config and group_config:
            self._validate_break_inheritance_flag(group_config, group)

        effective_config_for_group = self._merge_configs(common_config, group_config)
        debug(
            "*Effective* config common+group/subgroup: %s",
            to_str(effective_config_for_group),
        )

        return effective_config_for_group

    def _get_effective_subgroup_config(self, subgroup):

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
        # ...where a = merged_config("x", "x/y") and b = merged_config(a, "x/y/z")
        #

        effective_config = {}
        elements = subgroup.split("/")
        last_element = None
        for element in elements:
            if not last_element:
                effective_config = self._get_group_config(element)
                debug(
                    "First level config for '%s': %s", element, to_str(effective_config)
                )
                last_element = element
            else:
                next_level_subgroup = last_element + "/" + element
                next_level_subgroup_config = self._get_group_config(next_level_subgroup)
                debug(
                    "Config for '%s': %s",
                    next_level_subgroup,
                    to_str(next_level_subgroup_config),
                )

                if effective_config:
                    self._validate_break_inheritance_flag(effective_config, subgroup)
                elif not effective_config and next_level_subgroup_config:
                    self._validate_break_inheritance_flag(
                        next_level_subgroup_config, next_level_subgroup
                    )

                effective_config = self._merge_configs(
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

    def _get_group_config(self, group) -> dict:
        """
        :param group: group/subgroup
        :return: configuration for this group/subgroup or empty dict if not defined,
                 ignoring the case
        """
        return self._get_case_insensitively(
            self.get("projects_and_groups"), f"{group}/*"
        )
