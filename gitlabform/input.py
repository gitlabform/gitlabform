import sys

import cli_ui

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab.core import NotFoundException


class GroupsAndProjectsProvider:
    """
    For a query like "project/group", "group", "group/subgroup", ALL or ALL_DEFINED this
    class gets the effective lists of groups and project, taking into account skipped groups
    and projects and the fact that the group and project names case are somewhat case-sensitive.
    """

    def __init__(self, gitlab, configuration, include_archived_projects):
        self.gitlab = gitlab
        self.configuration = configuration
        self.include_archived_projects = include_archived_projects

    def get_groups_and_projects(self, target: str) -> (list, list):
        """
        :param target: "project/group", "group", "group/subgroup", ALL or ALL_DEFINED
        :return: tuple with lists of groups and projects that match the target query
        """
        groups = self._get_groups(target)
        projects = self._get_projects(target, groups)
        return groups, projects

    def _get_groups(self, target: str) -> list:

        if target == "ALL":
            # get all groups from GitLab and then remove the skipped ones
            requested_groups = self.gitlab.get_groups()
            effective_groups = self._remove_skipped_groups(requested_groups)

            return effective_groups

        if target == "ALL_DEFINED":

            # get all groups from configuration, but removed the skipped ones
            # before replacing group names with proper case of groups' *paths*
            # to do less requests to GitLab
            requested_groups = self.configuration.get_groups()
            effective_groups = self._remove_skipped_groups(requested_groups)
            effective_groups_proper_case = []
            for group in effective_groups:
                # in the config group names may not be written with correct case
                # so ensure that such group exists
                try:
                    group = self.gitlab.get_group_case_insensitive(group)
                    effective_groups_proper_case.append(group["full_path"])
                except NotFoundException:
                    cli_ui.error(
                        f"Configuration contains group {group} but it cannot be found in GitLab!"
                    )
                    sys.exit(EXIT_INVALID_INPUT)

            return effective_groups_proper_case

        try:
            # it may be a subgroup or a single group
            maybe_group = self.gitlab.get_group_case_insensitive(target)
            return [maybe_group["full_path"]]
        except NotFoundException:
            return []

    def _get_projects(self, target: str, groups: list) -> list:

        requested_projects = []

        if target == "ALL":
            # we already have all the groups
            pass

        if target == "ALL_DEFINED":
            # get projects explicitly defined in the configuration,
            requested_projects = self.configuration.get_projects()

        else:
            try:
                # it may be a project or a subgroup
                maybe_project = self.gitlab.get_project_case_insensitive(target)
                requested_projects = [maybe_project["path_with_namespace"]]
            except NotFoundException:
                pass

        # get the projects from the groups to process
        projects_from_groups = self._get_projects_from_groups(groups)

        # casting to set and back to list to deduplicate
        projects = sorted(list(set(requested_projects + projects_from_groups)))

        return self._remove_skipped_projects(projects)

    def _get_projects_from_groups(self, groups: list) -> list:
        # use set to deduplicate project list
        projects = set()
        for group in groups:
            for project in self.gitlab.get_projects(
                group, include_archived=self.include_archived_projects
            ):
                projects.add(project)
        return sorted(list(projects))

    def _remove_skipped_groups(self, groups: list) -> list:
        effective_groups = []
        for group in groups:
            if not self.configuration.is_group_skipped(group):
                effective_groups.append(group)
        return effective_groups

    def _remove_skipped_projects(self, projects: list) -> list:
        effective_projects = []
        for project in projects:
            if not self.configuration.is_project_skipped(project):
                effective_projects.append(project)
        return effective_projects
