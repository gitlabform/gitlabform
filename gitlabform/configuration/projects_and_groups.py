import logging

from gitlabform.configuration.core import ConfigurationCore, KeyNotFoundException

logger = logging.getLogger(__name__)


class ConfigurationProjectsAndGroups(ConfigurationCore):
    def __init__(self, config_path=None, config_string=None):
        super().__init__(config_path, config_string)

    def get_projects(self) -> list:
        """
        :return: sorted list of projects names
        """
        try:
            projects = []
            projects_and_groups = self.get("projects_and_groups")
            for element in projects_and_groups.keys():
                if element != "*" and not element.endswith("/*"):
                    projects.append(element)
            return sorted(projects)
        except KeyNotFoundException:
            raise ConfigNotFoundException

    def get_effective_config_for_project(self, group_and_project) -> dict:
        """
        :param group_and_project: "project_group/project_name"
        :return: merged configuration for this project, from common, group/subgroup and project level.
                 If project belongs to a subgroup, like "x/y/z", then it gets config from both group "x" as well
                 as subgroup "y".
                 Merging is additive.
        """

        common_config = self.get_config_common()
        logging.debug("Common config: %s" % common_config)

        group, project = group_and_project.rsplit("/", 1)
        if "/" in group:
            group_config = self.get_effective_subgroup_config(group)
        else:
            group_config = self.get_group_config(group)
        logging.debug("Effective group/subgroup config: %s" % group_config)

        project_config = self.get_project_config(group_and_project)
        logging.debug("Project config: %s" % project_config)

        common_and_group_config = self.merge_configs(common_config, group_config)
        logging.debug(
            "Effective config common+group/subgroup: %s" % common_and_group_config
        )

        effective_config = self.merge_configs(common_and_group_config, project_config)
        logging.debug(
            "Effective config common+group/subgroup+project: %s" % effective_config
        )

        return effective_config

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

    def merge_configs(self, more_general_config, more_specific_config) -> dict:
        """
        :return: merge more general config with more specific configs.
                 More specific config values take precedence over more general ones.
        """
        merged_config = {}

        for key in more_specific_config.keys() | more_general_config.keys():

            if key in more_general_config and key not in more_specific_config:
                merged_config[key] = more_general_config[key]
            elif key in more_specific_config and key not in more_general_config:
                merged_config[key] = more_specific_config[key]
            else:
                # overwrite more general config settings with more specific config
                merged_config[key] = {
                    **more_general_config[key],
                    **more_specific_config[key],
                }

        return merged_config

    def get_effective_config_for_group(self, group) -> dict:
        """
        :param group: "group_name"
        :return: merged configuration for this group, from common, group. Merging is additive.
        """

        common_config = self.get_config_common()
        logging.debug("Common config: %s" % common_config)

        group_config = self.get_group_config(group)
        logging.debug("Group config: %s" % group_config)

        # this project is not in any config - return empty config
        if not group_config and not common_config:
            return {}

        # this is simplistic, but for our config format should be enough for additive merge
        # of project, group and common configs

        # first merge common config with group configs
        for key in group_config.keys() | common_config.keys():

            if key in common_config and key not in group_config:
                group_config[key] = common_config[key]
            elif key in group_config and key not in common_config:
                group_config[key] = group_config[key]
            else:
                # overwrite common settings with group settings
                group_config[key] = {**common_config[key], **group_config[key]}

        return group_config

    def get_groups(self) -> list:
        """
        :return: sorted list of groups with configs
        """
        groups = []
        projects_and_groups = self.get("projects_and_groups")
        for element in projects_and_groups.keys():
            if element.endswith("/*"):
                # cut off that "/*"
                group_name = element[:-2]
                groups.append(group_name)
        return sorted(groups)

    def get_group_config(self, group) -> dict:
        """
        :param group: group/subgroup
        :return: literal configuration for this group/subgroup or empty dict if not defined
        """
        return self.get(f"projects_and_groups|{group}/*", {})

    def get_project_config(self, group_and_project) -> dict:
        """
        :param group_and_project: 'group/project'
        :return: literal configuration for this project or empty dict if not defined
        """
        return self.get(f"projects_and_groups|{group_and_project}", {})

    def get_config_common(self) -> dict:
        """
        :return: literal common configuration or empty dict if not defined
        """
        return self.get("projects_and_groups|*", {})

    def is_project_skipped(self, project) -> bool:
        """
        :return: if project is defined in the key with projects to skip
        """
        return project in self.get("skip_projects", [])

    def is_group_skipped(self, group):
        """
        :return: if group is defined in the key with groups to skip
        """
        return group in self.get("skip_groups", [])


class ConfigNotFoundException(Exception):
    pass
