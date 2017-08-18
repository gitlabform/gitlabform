import logging

from gitlabform.configuration.core import ConfigurationCore, KeyNotFoundException

logger = logging.getLogger(__name__)


class ConfigurationProjectsAndGroups(ConfigurationCore):

    def get_config_for_project(self, group_and_project) -> dict:
        """
        :param group_and_project: "project_name/project_group"
        :return: merged configuration for this project, from group level and project level. Merging is additive.
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

        if not project_config and not group_config:
            raise ConfigNotFoundException

        # this is simplistic, but for our config format should be enough for additive merge
        # of project and group configs
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

    def get_skip_projects(self) -> list:
        """
        :return: list of "project_name/project_group" to ignore
        """
        try:
            return self.get("skip_projects")
        except KeyNotFoundException:
            return []


class ConfigNotFoundException(Exception):
    pass
