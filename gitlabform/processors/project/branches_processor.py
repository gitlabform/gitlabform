import re
from typing import Optional
from logging import debug, info
from cli_ui import warning, fatal
from gitlab.v4.objects import Project, ProjectProtectedBranch
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabCreateError,
)
from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.strict = strict

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for branch in sorted(configuration["branches"]):
            branch_configuration: dict = self.transform_branch_config(
                configuration["branches"][branch]
            )

            self.process_branch_protection(project, branch, branch_configuration)

    def process_branch_protection(
        self, project: Project, branch_name: str, branch_config: dict
    ):
        """
        Process branch protection according to gitlabform config.
        """
        protected_branch: Optional[ProjectProtectedBranch] = None

        if not self.is_branch_name_wildcard(branch_name):
            try:
                branch = project.branches.get(branch_name)
            except GitlabGetError:
                message = f"Branch '{branch_name}' not found when processing it to be protected/unprotected!"
                if self.strict:
                    fatal(
                        message,
                        exit_code=EXIT_INVALID_INPUT,
                    )
                else:
                    warning(message)

        try:
            protected_branch = project.protectedbranches.get(branch_name)
        except GitlabGetError:
            message = f"The branch '{branch_name}' is not protected!"
            debug(message)

        if branch_config.get("protected"):
            if protected_branch and self._needs_update(
                protected_branch.attributes, branch_config
            ):
                # Need to unprotect the branch and then re-protect again using current config
                # Another option would be to "update" protected branch. But, GitLab's API for
                # updating protected branch requires retrieving id of the existing rule/config
                # such as 'allowed_to_push'. See: https://docs.gitlab.com/ee/api/protected_branches.html#example-update-a-push_access_level-record
                # This could involve more data processing. The data for updating vs creating a
                # protected branch is not the same. So, removing existing branch protection and
                # reconfiguring branch protection seems simpler.
                self.unprotect_branch(protected_branch)
                self.protect_branch(project, branch_name, branch_config)
            elif not protected_branch:
                self.protect_branch(project, branch_name, branch_config)
        elif protected_branch and not branch_config.get("protected"):
            self.unprotect_branch(protected_branch)

    def protect_branch(self, project: Project, branch: str, branch_config: dict):
        """
        Protect a branch using given config.
        Raise exception if running in strict mode.
        """

        debug("Setting branch '%s' as protected", branch)

        try:
            project.protectedbranches.create({"name": branch, **branch_config})
        except GitlabCreateError as e:
            message = f"Protecting branch '{branch}' failed! Error '{e.error_message}"

            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def unprotect_branch(self, protected_branch: ProjectProtectedBranch):
        """
        Unprotect a branch.
        Raise exception if running in strict mode.
        """

        debug("Setting branch '%s' as unprotected", protected_branch.name)

        try:
            # The delete method doesn't delete the actual branch.
            # It only unprotects the branch.
            protected_branch.delete()
        except GitlabDeleteError as e:
            message = f"Branch '{protected_branch.name}' could not be unprotected! Error '{e.error_message}"
            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def transform_branch_config(self, branch_config: dict):
        """
        The branch configuration in gitlabform supports passing users or group using username
        or group name but GitLab only supports their id. This method will transform the
        config by replacing them with ids.
        """

        for key in branch_config:
            if isinstance(branch_config[key], list):
                for item in branch_config[key]:
                    if isinstance(item, dict):
                        if "user" in item:
                            item["user_id"] = self.gl.get_user_id(item.pop("user"))
                        elif "group" in item:
                            item["group_id"] = self.gl.get_group_id(item.pop("group"))

        return branch_config

    @staticmethod
    def is_branch_name_wildcard(branch):
        return re.fullmatch(".*\\*.*", branch)
