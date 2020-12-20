import logging

from gitlabform.common.safe_dict import SafeDict
from gitlabform.configuration.config_chain import ConfigurationChain
from gitlabform.configuration.core import ConfigurationCore, KeyNotFoundException

logger = logging.getLogger(__name__)


class ConfigurationProjectsAndGroupsV2(ConfigurationCore):
    def __init__(self, config_path=None, config_string=None):
        super().__init__(config_path=config_path, config_string=config_string)
        self.config_chain = ConfigurationChain(self.get("projects_and_groups", []))

    def get_config_for_project(self, project) -> SafeDict:
        """
        :param project: project item
        :return: effective configuration for provided project
        """
        return self.config_chain.get_effective_config(project)

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
