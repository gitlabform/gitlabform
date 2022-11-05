from typing import Tuple

from cli_ui import fatal

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.input.core import Groups, Projects, OmissionReason
from gitlabform.input.groups import GroupsProvider

# from gitlabform.gitlab.core import NotFoundException


class ProjectsProvider(GroupsProvider):
    """
    For a query like "project/group", "group", "group/subgroup", ALL or ALL_DEFINED this
    class gets the effective lists of projects, taking into account skipped projects
    and the fact that the group and project names case are somewhat case-sensitive.

    Because the projects depend on groups requested, this class inherits GroupsProvider.
    """

    def __init__(self, gitlab, configuration, include_archived_projects):
        super().__init__(gitlab, configuration)
        self.include_archived_projects = include_archived_projects

    def get_projects(self, target: str) -> Projects:
        """
        :param target: "project/group", "group", "group/subgroup", ALL or ALL_DEFINED
        :return: Projects
        """

        groups = self.get_groups(target)

        if target not in ["ALL", "ALL_DEFINED"]:
            if len(groups.get_effective()) == 1:
                projects = self._get_projects(target, groups)
            else:
                projects = self._get_single_project(target)
        else:
            projects = self._get_projects(target, groups)

        return projects

    def _get_single_project(self, target: str) -> Projects:

        projects = Projects()

        # it may be a single project
        try:
            maybe_project = self.gitlab.get_project_case_insensitive(target)
            projects.add_requested([maybe_project["path_with_namespace"]])

        except Exception:  # TODO: this should be NotFoundException but it causes an import issue
            # it's a group or a subgroup - ignore it here
            pass

        return projects

    def _get_projects(self, target: str, groups: Groups) -> Projects:

        projects = Projects()

        # the source of projects are the *effective* requested groups
        (
            projects_from_groups,
            archived_projects_from_groups,
        ) = self._get_all_and_archived_projects_from_groups(groups.get_effective())
        projects.add_requested(projects_from_groups)
        projects.add_omitted(OmissionReason.ARCHIVED, archived_projects_from_groups)

        if target == "ALL_DEFINED":

            # in this case we also need to get the list of projects explicitly
            # defined in the configuration

            projects_from_configuration = self.configuration.get_projects()

            # ...but we don't need to re-check for being archived projects that we
            # already got from groups

            # TODO: this check should be case-insensitive
            projects_from_configuration_not_from_groups = [
                project
                for project in projects_from_configuration
                if project not in projects.requested
            ]

            archived_projects_from_configuration_not_from_groups = (
                self._verify_if_projects_exist_and_get_archived_projects(
                    projects_from_configuration_not_from_groups
                )
            )

            projects.add_requested(projects_from_configuration_not_from_groups)
            projects.add_omitted(
                OmissionReason.ARCHIVED,
                archived_projects_from_configuration_not_from_groups,
            )

        # TODO: consider checking for skipped earlier to avoid making requests for projects that will be skipped anyway
        projects.add_omitted(
            OmissionReason.SKIPPED, self._get_skipped_projects(projects.get_effective())
        )

        return projects

    def _verify_if_projects_exist_and_get_archived_projects(
        self, projects: list
    ) -> list:
        archived = []
        for project in projects:
            try:
                project_object = self.gitlab.get_project_case_insensitive(project)
                if project_object["archived"]:
                    archived.append(project_object["path_with_namespace"])
            except Exception:  # TODO: this should be NotFoundException but it causes an import issue
                fatal(
                    f"Configuration contains project {project} but it cannot be found in GitLab!",
                    exit_code=EXIT_INVALID_INPUT,
                )
        return archived

    def _get_all_and_archived_projects_from_groups(
        self, groups: list
    ) -> Tuple[list, list]:
        all = []
        archived = []
        for group in groups:
            if self.include_archived_projects:
                all += self.gitlab.get_projects(group, include_archived=True)
            else:
                project_objects = self.gitlab.get_projects(
                    group, include_archived=True, only_names=False
                )
                for project_object in project_objects:
                    project = project_object["path_with_namespace"]
                    all.append(project)
                    if project_object["archived"]:
                        archived.append(project)

        # deduplicate as we may have a group X and its subgroup X/Y in the groups list so the effective projects
        # may occur more than once
        return list(set(all)), list(set(archived))

    def _get_skipped_projects(self, projects: list) -> list:
        skipped = []
        for project in projects:
            if self.configuration.is_project_skipped(project):
                skipped.append(project)

        return skipped
