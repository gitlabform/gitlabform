from abc import ABC, abstractmethod

from cli_ui import fatal

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.lists import OmissionReason, Groups, Projects


# Groups and projects filters jobs is to omit some groups and projects that GitLabForm is requested
# to process for a speed-up.
#
# An example reason for omitting groups and projects is when they have an empty effective config.


class GroupsAndProjectsFilters:
    def __init__(self, configuration, group_processors, project_processors):
        self.configuration = configuration

        self.omit_empty_configs = OmitEmptyConfigs(configuration, group_processors, project_processors)
        # add next filters here

    def filter(self, groups: Groups, projects: Projects):
        self.omit_empty_configs.filter(groups, projects)
        # add next filters here


class GroupsAndProjectsFilter(ABC):
    @abstractmethod
    def filter(self, groups: Groups, projects: Projects):
        pass


class OmitEmptyConfigs(GroupsAndProjectsFilter):
    """
    One of the reasons groups or project can be omitted from processing is when they have an empty effective config.

    For example with a config like:

    projects_and_groups:
      *:
        group_variables:
          foobar:
            key: "a key"
            value: "the value"

    ...and a request query "foo/bar" that points to a project "bar" in a group "foo", the effective config
    is empty, as "group_variables" is a group-level configuration and "foo/bar" is a project.
    """

    def __init__(self, configuration, group_processors, project_processors):
        self.configuration = configuration
        self.group_processors = group_processors
        self.project_processors = project_processors

        if not self.configuration.get("projects_and_groups", {}):
            fatal(
                "Configuration has to contain non-empty 'projects_and_groups' key.",
                exit_code=EXIT_INVALID_INPUT,
            )

    def filter(self, groups: Groups, projects: Projects) -> None:
        """
        :param groups: list of groups (and possibly subgroups)
        :param projects: list of projects
        """

        groups_with_empty_configs = []
        for group in groups.get_effective():
            if self._group_has_empty_effective_config(group):
                groups_with_empty_configs.append(group)
        groups.add_omitted(OmissionReason.EMPTY, groups_with_empty_configs)

        projects_with_empty_configs = []
        for project in projects.get_effective():
            if self._project_has_empty_effective_config(project):
                projects_with_empty_configs.append(project)
        projects.add_omitted(OmissionReason.EMPTY, projects_with_empty_configs)

    def _group_has_empty_effective_config(self, group: str) -> bool:
        """
        :param group: group/subgroup
        :return: if given group/subgroup has no config that can be processed
                 by any group-level processors
        """
        config_for_group = self.configuration.get_effective_config_for_group(group)
        for configuration_name in config_for_group.keys():
            if configuration_name in self.group_processors.get_configuration_names():
                return False
        return True

    def _project_has_empty_effective_config(self, project: str) -> bool:
        """
        :param project: 'group/project'
        :return: if given project has no config that can be processed
                 by any project-level processors
        """
        config_for_project = self.configuration.get_effective_config_for_project(project)
        for configuration_name in config_for_project.keys():
            if configuration_name in self.project_processors.get_configuration_names():
                return False
        return True
