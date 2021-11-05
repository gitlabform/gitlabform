from cli_ui import fatal

from gitlabform import EXIT_INVALID_INPUT, Groups, Projects


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
            fatal(
                "Configuration has to contain non-empty 'projects_and_groups' key.",
                exit_code=EXIT_INVALID_INPUT,
            )

    def omit_groups_and_projects_with_empty_configs(
        self, groups: Groups, projects: Projects
    ) -> (Groups, Projects):
        """
        :param groups: list of groups (and possibly subgroups)
        :param projects: list of projects
        :return: a tuple with lists of:
          * groups that have configs that can be processed by some group-level processors
          * projects that have configs that can be processed by some project-level processors
          * groups that DON'T have configs that can be processed by some group-level processors
          * projects that DON'T have configs that can be processed by some project-level processors
        """

        groups_with_empty_configs = []
        for group in groups.get_effective():
            if self.group_has_empty_effective_config(group):
                groups_with_empty_configs.append(group)
        groups.add_omitted("empty effective config", groups_with_empty_configs)

        projects_with_empty_configs = []
        for project in projects.get_effective():
            if self.project_has_empty_effective_config(project):
                projects_with_empty_configs.append(project)
        projects.add_omitted("empty effective config", projects_with_empty_configs)

        return groups, projects

    def group_has_empty_effective_config(self, group: str) -> bool:
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

    def project_has_empty_effective_config(self, project: str) -> bool:
        """
        :param project: 'group/project'
        :return: if given project has no config that can be processed
                 by any project-level processors
        """
        config_for_project = self.configuration.get_effective_config_for_project(
            project
        )
        for configuration_name in config_for_project.keys():
            if configuration_name in self.project_processors.get_configuration_names():
                return False
        return True
