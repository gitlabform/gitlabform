import logging

from gitlabform.configuration.core import ConfigurationCore, KeyNotFoundException

logger = logging.getLogger(__name__)


class ConfigurationProjectsAndGroups(ConfigurationCore):

    def get_projects(self) -> list:
        """
        :return: sorted list of projects with configs
        """
        try:
            return sorted(self.get("project_settings").keys())
        except KeyNotFoundException:
            raise ConfigNotFoundException

    def get_effective_config_for_project(self, group_and_project) -> dict:
        """
        :param group_and_project: "project_name/project_group"
        :return: merged configuration for this project, from common, group and project level. Merging is additive.
        """
        try:
            project_config = self.get("project_settings|%s" % group_and_project)
        except KeyNotFoundException:
            project_config = {}

        logging.debug("Project config: %s" % project_config)

        group, _ = group_and_project.split('/')
        try:
            group_config = self.get_config_for_group(group)
        except ConfigNotFoundException:
            group_config = {}

        logging.debug("Group config: %s" % group_config)

        try:
            common_config = self.get("common_settings")
        except KeyNotFoundException:
            common_config = {}

        if not project_config and not group_config and not common_config:
            raise ConfigNotFoundException

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

        # ...and then groups config with project configs
        for key in project_config.keys() | group_config.keys():

            if key in group_config and key not in project_config:
                project_config[key] = group_config[key]
            elif key in project_config and key not in group_config:
                project_config[key] = project_config[key]
            else:
                # overwrite group settings with project ones
                project_config[key] = {**group_config[key], **project_config[key]}

        return project_config

    def get_groups(self) -> list:
        """
        :return: sorted list of groups with configs
        """
        try:
            return sorted(self.get("group_settings").keys())
        except KeyNotFoundException:
            raise ConfigNotFoundException

    def get_config_for_group(self, group) -> dict:
        """
        :param group: project_group
        :return: configuration for this group
        """
        try:
            return self.get("group_settings|%s" % group)
        except KeyNotFoundException:
            raise ConfigNotFoundException

    def get_config_common(self) -> dict:
        """
        :return: common configuration
        """
        try:
            return self.get("common_settings")
        except KeyNotFoundException:
            raise ConfigNotFoundException

    def get_skip_projects(self) -> list:
        """
        :return: list of "project_name/project_group" to ignore
        """
        try:
            return self.get("skip_projects")
        except KeyNotFoundException:
            return []

    def get_skip_groups(self) -> list:
        """
        :return: list of "project_group" to ignore
        """
        try:
            return self.get("skip_groups")
        except KeyNotFoundException:
            return []


class ConfigNotFoundException(Exception):
    pass
