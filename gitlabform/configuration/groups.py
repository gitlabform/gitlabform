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

        common_config: dict = self.get_common_config()
        debug("*Effective* common config: %s", to_str(common_config))

        if "/" in group:
            group_config = self._get_effective_subgroup_config(group, has_parent_context=bool(common_config))
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

    def _get_effective_subgroup_config(self, subgroup, has_parent_context: bool = False):
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
        # ``inherit: false`` on a layer is rejected only when no parent exists above it
        # (no common config and no non-empty accumulated ancestor config).

        effective_config: dict = {}
        elements = subgroup.split("/")
        current_path = None
        for element in elements:
            current_path = element if current_path is None else current_path + "/" + element
            current_layer = self._get_group_config(current_path)
            debug("Config for '%s': %s", current_path, to_str(current_layer))

            has_ancestor_context = has_parent_context or bool(effective_config)
            if current_layer and not has_ancestor_context:
                self._validate_break_inheritance_flag(current_layer, current_path)

            if not effective_config:
                effective_config = current_layer
            else:
                effective_config = self._merge_configs(effective_config, current_layer)
            debug("Effective config at '%s': %s", current_path, to_str(effective_config))

        return effective_config

    def _get_group_config(self, group) -> dict:
        """
        :param group: group/subgroup
        :return: configuration for this group/subgroup or empty dict if not defined,
                 ignoring the case
        """
        return self._get_case_insensitively(self.get("projects_and_groups"), f"{group}/*")

    def has_group_section_defined_locally(self, group: str, section_name: str) -> bool:
        """
        :return: True when ``section_name`` is defined directly on ``group/*`` in the config.
        """
        return section_name in self._get_group_config(group)
