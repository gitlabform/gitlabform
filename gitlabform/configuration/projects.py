from abc import ABC

import functools
from cli_ui import debug

from gitlabform.configuration import ConfigurationGroups
from gitlabform.util import to_str


class ConfigurationProjects(ConfigurationGroups, ABC):
    """
    Gets the projects, skipped projects and their effective configuration.

    ConfigurationGroups is an ancestor of this class because the effective project configuration
    depends on the groups (and common) configuration.
    """

    def get_projects(self) -> list:
        """
        :return: sorted list of projects names, that are EXPLICITLY defined in the config
        """
        projects = []
        projects_and_groups = self.get("projects_and_groups")
        for element in projects_and_groups.keys():
            if element != "*" and not element.endswith("/*"):
                projects.append(element)
        return sorted(projects)

    def is_project_skipped(self, project) -> bool:
        """
        :return: if project is defined in the key with projects to skip,
                 ignoring the case
        """
        return self._is_skipped_case_insensitively(self.get("skip_projects", []), project)

    @functools.lru_cache()
    def get_effective_config_for_project(self, group_and_project) -> dict:
        """
        :param group_and_project: "project_group/project_name"
        :return: merged configuration for this project, from common, group/subgroup and project level.
                 If project belongs to a subgroup, like "x/y/z", then it gets config from both group "x" as well
                 as subgroup "y".
                 Merging is additive.
        """

        group, _ = group_and_project.rsplit("/", 1)

        effective_config_for_group = self.get_effective_config_for_group(group)

        project_config = self._get_project_config(group_and_project)
        debug("Project config: %s", to_str(project_config))

        if not effective_config_for_group and project_config:
            self._validate_break_inheritance_flag(project_config, group_and_project)

        effective_config_for_project = self._merge_configs(
            effective_config_for_group,
            project_config,
        )
        debug(
            "*Effective* config common+group/subgroup+project: %s",
            to_str(effective_config_for_project),
        )

        return effective_config_for_project

    def _get_project_config(self, group_and_project) -> dict:
        """
        :param group_and_project: 'group/project'
        :return: configuration for this project or empty dict if not defined,
                 ignoring the case
        """
        return self._get_case_insensitively(self.get("projects_and_groups"), group_and_project)
