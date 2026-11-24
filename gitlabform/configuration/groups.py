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
        groups = set()
        projects_and_groups = self.get("projects_and_groups")
        for element in projects_and_groups.keys():
            if element.endswith("/*"):
                groups.add(element[:-2])
            elif element.endswith("/"):
                groups.add(element[:-1])
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
        :param group: "group_name" or "group/subgroup/..."
        :return: merged configuration for this group. Layers are merged from the most general to the most
                 specific: common ("*"), then "x/*", "x/y/*", ..., and finally the non-recursive "x/y/" key.
                 Merging is additive, but ``inherit: false`` in any layer discards that section from ALL
                 layers above it, including the common config.
        """
        # Check if group must be skipped
        if self.is_group_skipped(group):
            debug(f"Group {group} is skipped, returning empty config")
            return {}

        # Merge into a copy so callers never get (and mutate) the shared common config object
        effective_config: dict = self._merge_configs({}, self.get_common_config())
        debug("*Effective* common config: %s", to_str(effective_config))

        # "x/y/z" -> ["x", "x/y", "x/y/z"] recursive layers, followed by the exact "x/y/z/" layer
        elements = group.split("/")
        paths = ["/".join(elements[: i + 1]) for i in range(len(elements))]
        layers = [(path, self._get_group_config(path)) for path in paths]
        layers.append((f"{group}/", self._get_group_config(group, exact=True)))

        for layer_name, layer in layers:
            if not layer:
                continue
            debug("Config for '%s': %s", layer_name, to_str(layer))
            # ``inherit: false`` is rejected only when there is nothing above this layer to break from
            if not effective_config:
                self._validate_break_inheritance_flag(layer, layer_name)
            effective_config = self._merge_configs(effective_config, layer)
            debug("*Effective* config after '%s': %s", layer_name, to_str(effective_config))

        return effective_config

    def _get_group_config(self, group, exact=False) -> dict:
        """
        :param group: group/subgroup
        :param exact: if True, look up the non-recursive "group/" key instead of "group/*"
        :return: configuration for this group/subgroup or empty dict if not defined,
                 ignoring the case
        """
        suffix = "/" if exact else "/*"
        return self._get_case_insensitively(self.get("projects_and_groups"), f"{group}{suffix}")
