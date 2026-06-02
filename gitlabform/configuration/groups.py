from abc import ABC

import functools
from logging import debug

from gitlabform.configuration import ConfigurationCommon
from gitlabform.configuration.core import ConfigurationState
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
                groups.append(element[:-2])
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
        # Check if group must be skipped
        if self.is_group_skipped(group):
            debug(f"Group {group} is skipped, returning empty config")
            return {}

        group_state = self._get_group_state(group)
        debug("*Effective* config common+group/subgroup: %s", to_str(group_state.effective_config))

        return group_state.effective_config

    @functools.lru_cache()
    def _get_group_state(self, group) -> ConfigurationState:
        debug(
            "Building group state for '%s'",
            group,
        )

        common_state = self._get_common_state()
        debug("*Effective* common config: %s", to_str(common_state.effective_config))
        debug("*Propagatable* common config: %s", to_str(common_state.propagatable_config))

        if "/" in group:
            return self._get_effective_subgroup_state(group, common_state)

        group_config = self._get_group_config(group)
        debug("*Raw* group config: %s", to_str(group_config))

        if not common_state.propagatable_config and group_config:
            self._validate_break_inheritance_flag(group_config, group)

        return self._build_configuration_state(common_state.propagatable_config, group_config)

    def _get_effective_subgroup_state(self, subgroup: str, common_state: ConfigurationState) -> ConfigurationState:
        """
        Return the configuration state for ``subgroup`` across the whole hierarchy.
        """
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
        elements = subgroup.split("/")
        last_element = None
        inherited_state = common_state

        for element in elements:
            if not last_element:
                first_level_group_config = self._get_group_config(element)
                debug("First level config for '%s': %s", element, to_str(first_level_group_config))

                if not inherited_state.propagatable_config and first_level_group_config:
                    self._validate_break_inheritance_flag(first_level_group_config, element)

                inherited_state = self._build_configuration_state(
                    inherited_state.propagatable_config,
                    first_level_group_config,
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

                if not inherited_state.propagatable_config and next_level_subgroup_config:
                    self._validate_break_inheritance_flag(next_level_subgroup_config, next_level_subgroup)

                inherited_state = self._build_configuration_state(
                    inherited_state.propagatable_config,
                    next_level_subgroup_config,
                )
                debug(
                    "Merged previous level config for '%s' with config for '%s': %s",
                    last_element,
                    next_level_subgroup,
                    to_str(inherited_state.effective_config),
                )
                last_element = next_level_subgroup

        return inherited_state

    def _get_group_config(self, group) -> dict:
        """
        :param group: group/subgroup
        :return: configuration for this group/subgroup or empty dict if not defined,
                 ignoring the case
        """
        return self._get_case_insensitively(self.get("projects_and_groups"), f"{group}/*")
