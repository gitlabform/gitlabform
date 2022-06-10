import functools
from logging import debug

from gitlabform.configuration.groups import ConfigurationGroups
from gitlabform.ui import to_str


class ConfigurationProjectsAndGroups(ConfigurationGroups):
    def __init__(self, config_path=None, config_string=None):
        super().__init__(config_path, config_string)

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

    @functools.lru_cache()
    def get_effective_config_for_project(self, group_and_project) -> dict:
        """
        :param group_and_project: "project_group/project_name"
        :return: merged configuration for this project, from common, group/subgroup and project level.
                 If project belongs to a subgroup, like "x/y/z", then it gets config from both group "x" as well
                 as subgroup "y".
                 Merging is additive.
        """

        common_config = self.get_common_config()
        debug("Common config: %s", to_str(common_config))

        group, project = group_and_project.rsplit("/", 1)
        if "/" in group:
            group_config = self.get_effective_subgroup_config(group)
        else:
            group_config = self.get_group_config(group)
        debug("Effective group/subgroup config: %s", to_str(group_config))

        if common_config:
            # since common is not included in the projects array,
            # we define it here
            section_name = "*"
            self.validate_break_inheritance_flag(common_config, section_name)
        elif not common_config and group_config:
            self.validate_break_inheritance_flag(group_config, group)

        project_config = self.get_project_config(group_and_project)
        debug("Project config: %s", to_str(project_config))

        if not common_config and not group_config and project_config:
            self.validate_break_inheritance_flag(project_config, project)

        common_and_group_config = self.merge_configs(
            common_config,
            group_config,
        )
        debug(
            "Effective config common+group/subgroup: %s",
            to_str(common_and_group_config),
        )

        effective_config = self.merge_configs(
            common_and_group_config,
            project_config,
        )
        debug(
            "Effective config common+group/subgroup+project: %s",
            to_str(effective_config),
        )

        return effective_config


class EmptyConfigException(Exception):
    pass
