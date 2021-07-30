import sys

import cli_ui

from gitlabform import EXIT_INVALID_INPUT


class NonEmptyConfigsProvider(object):
    """
    To speed up the processing of possibly long groups and projects lists we want to quickly remove
    the ones that have an empty effective config.

    For example with a config like:

    projects_and_groups:
      *:
        group_secret_variables:
          foobar:
            key: "a key"
            value: "the value"

    ...and a request query "foo/bar" that points to a project "bar" in a group "foo", the effective config
    is empty, as "group_secret_variables" is a group-level configuration and "foo/bar" is a project.
    """

    def __init__(self, configuration, group_processors, project_processors):
        self.configuration = configuration
        self.group_processors = group_processors
        self.project_processors = project_processors

        if not self.configuration.get("projects_and_groups", {}):
            cli_ui.error(
                "Configuration has to contain non-empty 'projects_and_groups' key."
            )
            sys.exit(EXIT_INVALID_INPUT)

    def get_groups_and_projects_with_non_empty_configs(
        self, groups: list, projects: list
    ) -> (list, list, list, list):
        """
        :param groups: list of groups (and possibly subgroups)
        :param projects: list of projects
        :return: a tuple with lists of:
          * groups that have configs that can be processed by some group-level processors
          * projects that have configs that can be processed by some project-level processors
          * groups that DON'T have configs that can be processed by some group-level processors
          * projects that DON'T have configs that can be processed by some project-level processors
        """
        groups_with_non_empty_configs = []
        projects_with_non_empty_configs = []
        groups_with_empty_configs = []
        projects_with_empty_configs = []

        for group in groups:
            if self.group_has_non_empty_effective_config(group):
                groups_with_non_empty_configs.append(group)
            else:
                groups_with_empty_configs.append(group)
        for project in projects:
            if self.project_has_non_empty_effective_config(project):
                projects_with_non_empty_configs.append(project)
            else:
                projects_with_empty_configs.append(project)

        return (
            groups_with_non_empty_configs,
            projects_with_non_empty_configs,
            groups_with_empty_configs,
            projects_with_empty_configs,
        )

    def group_has_non_empty_effective_config(self, group: str) -> bool:
        """
        :param group: group/subgroup
        :return: if given group/subgroup has an config that can be processed
                 by some group-level processors
        """
        config_for_group = self.configuration.get_effective_config_for_group(group)
        for configuration_name in config_for_group.keys():
            if configuration_name in self.group_processors.get_configuration_names():
                return True
        return False

    def project_has_non_empty_effective_config(self, project: str) -> bool:
        """
        :param project: 'group/project'
        :return: if given project has a config that can be processed
                 by some project-level processors
        """
        config_for_project = self.configuration.get_effective_config_for_project(
            project
        )
        for configuration_name in config_for_project.keys():
            if configuration_name in self.project_processors.get_configuration_names():
                return True
        return False
