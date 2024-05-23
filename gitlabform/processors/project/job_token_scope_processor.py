from typing import List

from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessor
from cli_ui import warning, info, debug

from gitlab.v4.objects import Project, ProjectJobTokenScope


class JobTokenScopeProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("job_token_scope", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        job_token_config = configuration.get("job_token_scope", {})
        debug(f"Job Token Scope config: {job_token_config}")

        project = self.gl.get_project_by_path_cached(project_and_group)
        job_token_scope = project.job_token_scope.get()

        limit_access_state_updated = self._process_limit_access_to_this_project_setting(
            job_token_config, job_token_scope
        )

        if limit_access_state_updated:
            # Refresh has no return but produces same result as project.job_token_scope.get()
            # -> refreshes job_token_scope state with latest changes
            job_token_scope.refresh()

        allowlist_config = job_token_config.get("allowlist", {})
        debug(f"configuration allowlist: {allowlist_config}")

        info("Processing Job Token allowlist")

        enforce = allowlist_config.get("enforce", False)

        self._process_groups(
            job_token_scope, allowlist_config.get("groups", []), enforce
        )

        self._process_projects(
            project, job_token_scope, allowlist_config.get("projects", []), enforce
        )

    @staticmethod
    def _process_limit_access_to_this_project_setting(
        configuration: dict, job_token_scope: ProjectJobTokenScope
    ):
        limit_access_to_this_project: bool = configuration.get(
            "limit_access_to_this_project", True
        )

        if limit_access_to_this_project != job_token_scope.inbound_enabled:
            info(
                f"Updating project job token scope to limit access: {limit_access_to_this_project}"
            )
            job_token_scope.enabled = limit_access_to_this_project
            job_token_scope.save()
            return True
        else:
            info(f"Job Token Scope does not need updating")
            return False

    def _process_projects(
        self,
        project: Project,
        job_token_scope: ProjectJobTokenScope,
        projects_allowlist: List,
        enforce: bool,
    ):
        if not projects_allowlist and enforce:
            warning(
                "Process will remove existing projects from allowlist, as none set in configuration"
            )

        existing_allowlist = job_token_scope.allowlist.list(get_all=True)

        project_ids_to_allow = self._get_target_project_ids_from_config(
            projects_allowlist
        )

        allowlist_updated = False
        if len(project_ids_to_allow) > 0:
            allowlist_updated = self._add_projects_to_allowlist(
                project, job_token_scope, existing_allowlist, project_ids_to_allow
            )

        if enforce:
            if allowlist_updated:
                # Refresh has no return but produces same result as project.job_token_scope.get()
                # -> refreshes job_token_scope state with latest changes
                job_token_scope.refresh()

            info(
                "Enforce enabled, removing projects no longer defined in config from allowlist"
            )
            self._remove_projects_from_allowlist(
                project, job_token_scope, existing_allowlist, project_ids_to_allow
            )

    def _process_groups(
        self,
        job_token_scope: ProjectJobTokenScope,
        groups_allowlist: List,
        enforce: bool,
    ):
        if not groups_allowlist and enforce:
            warning(
                "Process will remove existing groups from allowlist, as none set in configuration"
            )

        existing_allowlist = job_token_scope.groups_allowlist.list(get_all=True)

        group_ids_to_allow = self._get_target_group_ids_from_config(groups_allowlist)

        allowlist_updated = False
        if len(group_ids_to_allow) > 0:
            allowlist_updated = self._add_groups_to_allowlist(
                job_token_scope, existing_allowlist, group_ids_to_allow
            )

        if enforce:
            if allowlist_updated:
                # Refresh has no return but produces same result as project.job_token_scope.get()
                # -> refreshes job_token_scope state with latest changes
                job_token_scope.refresh()

            info(
                "Enforce enabled, removing groups no longer defined in config from allowlist"
            )
            self._remove_groups_from_allowlist(
                job_token_scope, existing_allowlist, group_ids_to_allow
            )

    def _remove_groups_from_allowlist(
        self,
        job_token_scope: ProjectJobTokenScope,
        existing_allowlist,
        target_group_ids: List,
    ):
        allowlist_updated = False
        group_ids_to_remove = self._get_ids_to_remove_from_allowlist(
            existing_allowlist, target_group_ids
        )
        for group_id in group_ids_to_remove:
            allowlist_updated = True
            job_token_scope.groups_allowlist.delete(group_id)
            info("Deleted group %s from allowlist", group_id)

        if allowlist_updated:
            debug("Saving removed Groups allowlist changes")
            job_token_scope.save()

    @staticmethod
    def _add_groups_to_allowlist(
        job_token_scope, existing_allowlist, group_ids_listed_in_config
    ):
        allowlist_updated = False

        for group_id in group_ids_listed_in_config:
            if any(allowed.get_id() == group_id for allowed in existing_allowlist):
                # If already in allowlist, do nothing
                debug(f"{group_id} already in Groups allowlist")
                continue

            allowlist_updated = True
            job_token_scope.groups_allowlist.create({"target_group_id": group_id})
            info(f"Added Group {group_id} to allowlist")

        # If we have added something new to the allowlist then save the scope otherwise save API calls
        if allowlist_updated:
            debug("Saving added Groups allowlist changes")
            job_token_scope.save()
            return True
        else:
            return False

    @staticmethod
    def _add_projects_to_allowlist(
        project, job_token_scope, existing_allowlist, project_ids_listed_in_config
    ):
        allowlist_state_updated = False

        for project_id in project_ids_listed_in_config:
            if project_id != project.id:
                if any(
                    allowed.get_id() == project_id for allowed in existing_allowlist
                ):
                    # If already in allowlist, do nothing
                    debug(f"{project_id} already in Projects allowlist")
                    continue

                allowlist_state_updated = True
                job_token_scope.allowlist.create({"target_project_id": project_id})
                info(f"Added Project {project_id} to allowlist")

        # If we have added something new to the allowlist then save the scope otherwise save API calls
        if allowlist_state_updated:
            debug("Saving added Projects allowlist changes")
            job_token_scope.save()
            return True
        else:
            return False

    def _remove_projects_from_allowlist(
        self,
        project: Project,
        job_token_scope: ProjectJobTokenScope,
        existing_allowlist,
        target_project_ids: List,
    ):
        removed_items_from_allowlist = False
        project_ids_to_remove = self._get_ids_to_remove_from_allowlist(
            existing_allowlist, target_project_ids
        )
        for project_id in project_ids_to_remove:
            if project_id != project.id:
                removed_items_from_allowlist = True
                job_token_scope.allowlist.delete(project_id)
                info("Deleted project %s from allowlist", project_id)

        if removed_items_from_allowlist:
            debug("Saving removed Projects allowlist changes")
            job_token_scope.save()

    @staticmethod
    def _get_ids_to_remove_from_allowlist(existing_allowlist, target_ids: List):
        ids_to_remove = []

        for allowed in existing_allowlist:
            if allowed.id not in target_ids:
                ids_to_remove.append(allowed.id)

        return ids_to_remove

    def _get_target_project_ids_from_config(self, projects_allowlist: List):
        target_project_ids = []

        for target_project_or_id in projects_allowlist:
            target_project = self.gl.get_project_by_path_cached(target_project_or_id)
            target_project_ids.append(target_project.id)

        return target_project_ids

    def _get_target_group_ids_from_config(self, groups_allowlist: List):
        target_group_ids = []

        for target_group_or_id in groups_allowlist:
            target_group = self.gl.get_group_by_path_cached(target_group_or_id)
            target_group_ids.append(target_group.id)

        return target_group_ids
