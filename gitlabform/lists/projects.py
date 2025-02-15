from typing import Optional, Tuple
from logging import debug
from cli_ui import fatal

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.lists import OmissionReason, Groups, Projects
from gitlabform.lists.groups import GroupsProvider

from gitlabform.gitlab.core import NotFoundException


class ProjectsProvider(GroupsProvider):
    """
    For a query like "project/group", "group", "group/subgroup", ALL or ALL_DEFINED this
    class gets the effective lists of projects, taking into account skipped projects
    and the fact that the group and project names case are somewhat case-sensitive.

    Because the projects depend on groups requested, this class inherits GroupsProvider.
    """

    def __init__(self, gitlab, configuration, include_archived_projects, recurse_subgroups):
        super().__init__(gitlab, configuration, recurse_subgroups)
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

        except NotFoundException:
            debug("Could not find '%s'", target)
            if project_transfer_source := self._get_project_transfer_source_from_config(target):
                if self._find_project_transfer_source_in_gitlab(project_transfer_source):
                    projects.add_requested([target])
                else:
                    fatal(
                        f"""Configuration contains project {target} to be transferred from {project_transfer_source}
                            but the source project cannot be found in GitLab!""",
                        exit_code=EXIT_INVALID_INPUT,
                    )

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

        projects_from_configuration = self.configuration.get_projects()

        # TODO: this check should be case-insensitive
        projects_from_configuration_not_from_groups = [
            project for project in projects_from_configuration if project not in projects.requested
        ]

        if target == "ALL_DEFINED":
            # in this case we also need to get the list of projects explicitly
            # defined in the configuration, but we don't need to re-check for
            # being archived projects that we already got from groups

            archived_projects_from_configuration_not_from_groups = (
                self._verify_if_projects_exist_and_get_archived_projects(projects_from_configuration_not_from_groups)
            )

            projects.add_requested(projects_from_configuration_not_from_groups)
            projects.add_omitted(
                OmissionReason.ARCHIVED,
                archived_projects_from_configuration_not_from_groups,
            )
        else:
            # in all other cases, we also need to look for projects in the config
            # that are being transferred to a different namespace
            for project in projects_from_configuration_not_from_groups:
                # if the target is a group, and the project is not in the group
                if len(groups.get_effective()) == 1 and target != "ALL" and target != project.rsplit("/", 1)[0]:
                    debug(
                        "Ignore project '%s', since it's not in target group '%s",
                        project,
                        target,
                    )
                else:
                    if (maybe_projects := self._get_single_project(project)) and len(
                        maybe_projects.get_effective()
                    ) != 0:
                        projects.add_requested([project])

        # TODO: consider checking for skipped earlier to avoid making requests for projects that will be skipped anyway
        projects.add_omitted(OmissionReason.SKIPPED, self._get_skipped_projects(projects.get_effective()))

        return projects

    def _verify_if_projects_exist_and_get_archived_projects(self, projects: list) -> list:
        archived = []
        for project in projects:
            try:
                project_object = self.gitlab.get_project_case_insensitive(project)
                if project_object["archived"]:
                    archived.append(project_object["path_with_namespace"])
            except NotFoundException:
                debug("Could not find '%s'", project)
                if project_transfer_source := self._get_project_transfer_source_from_config(project):
                    source_project = self._find_project_transfer_source_in_gitlab(project_transfer_source)
                    if source_project:
                        if source_project["archived"]:
                            archived.append(project)
                    else:
                        fatal(
                            f"""Configuration contains project {project} to be transferred from {project_transfer_source}
                                but the source project cannot be found in GitLab!""",
                            exit_code=EXIT_INVALID_INPUT,
                        )
                else:
                    fatal(
                        f"Configuration contains project {project} but it cannot be found in GitLab and it's not a project that is configured to be transferred from elsewhere.",
                        exit_code=EXIT_INVALID_INPUT,
                    )

        return archived

    def _get_all_and_archived_projects_from_groups(self, groups: list) -> Tuple[list, list]:
        all = []
        archived = []
        for group in groups:
            if self.include_archived_projects:
                all += self.gitlab.get_projects(group, include_archived=True)
            else:
                project_objects = self.gitlab.get_projects(group, include_archived=True, only_names=False)
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

    def _get_project_transfer_source_from_config(self, project: str) -> Optional[str]:
        try:
            debug(
                "Checking if project '%s' needs to be transferred from elsewhere",
                project,
            )
            project_transfer_source = self.configuration.config["projects_and_groups"][project]["project"][
                "transfer_from"
            ]
            debug(
                "Project '%s' needs to be transferred from '%s'",
                project,
                project_transfer_source,
            )
        except KeyError:
            debug("'%s' is not a project needing to be transferred", project)
            return None

        return project_transfer_source

    def _find_project_transfer_source_in_gitlab(self, project_transfer_source: str) -> Optional[dict]:
        try:
            debug(
                "Checking if project transfer source ('%s') exists in GitLab",
                project_transfer_source,
            )
            maybe_project = self.gitlab.get_project_case_insensitive(project_transfer_source)
            debug(
                "Project transfer source ('%s') exists",
                project_transfer_source,
            )
        except NotFoundException:
            debug(
                "Project transfer source ('%s') does not exist",
                project_transfer_source,
            )
            return None

        return maybe_project
