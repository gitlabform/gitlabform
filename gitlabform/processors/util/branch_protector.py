from logging import debug
from cli_ui import warning, fatal

from gitlabform import EXIT_PROCESSING_ERROR, EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException


class BranchProtector(object):

    old_api_keys = ["developers_can_push", "developers_can_merge"]
    new_api_keys = [
        "push_access_level",
        "merge_access_level",
        "unprotect_access_level",
    ]

    def __init__(self, gitlab: GitLab, strict: bool):
        self.gitlab = gitlab
        self.strict = strict

    def apply_branch_protection_configuration(
        self, project_and_group, configuration, branch
    ):
        try:
            requested_configuration = configuration["branches"][branch]

            if requested_configuration.get("protected"):
                self.protect_branch(project_and_group, configuration, branch)
            else:
                self.unprotect_branch(project_and_group, branch)

        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def protect_branch(self, project_and_group, configuration, branch):
        try:
            requested_configuration = configuration["branches"][branch]

            config_type = self.get_branch_protection_config_type(
                project_and_group, requested_configuration, branch
            )

            if config_type == "old":

                self.protect_using_old_api(
                    requested_configuration, project_and_group, branch
                )

            elif config_type == "new":

                if self.configuration_update_needed(
                    requested_configuration, project_and_group, branch
                ):
                    self.protect_using_new_api(
                        requested_configuration, project_and_group, branch
                    )
                else:
                    debug(
                        "Skipping set branch '%s' access levels because they're already set"
                    )

            if "code_owner_approval_required" in requested_configuration:

                self.set_code_owner_approval_required(
                    requested_configuration, project_and_group, branch
                )

        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def unprotect_branch(self, project_and_group, branch):
        try:
            debug("Setting branch '%s' as unprotected", branch)

            # we don't know if the old or new API was used to protect
            # so use both when unprotecting

            # ...except for wildcard branch names - there are not supported by the old API
            if "*" not in branch:
                self.gitlab.unprotect_branch(project_and_group, branch)

            self.gitlab.unprotect_branch_new_api(project_and_group, branch)

        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def get_branch_protection_config_type(
        self, project_and_group, requested_configuration, branch
    ):

        # for new API any keys needs to be defined...
        if any(key in requested_configuration for key in self.new_api_keys):
            return "new"

        # ...while for the old API - *all* of them
        if all(key in requested_configuration for key in self.old_api_keys):
            return "old"

        else:
            fatal(
                f"Invalid configuration for protecting branches in project '{project_and_group}',"
                f" branch '{branch}' - missing keys.",
                exit_code=EXIT_INVALID_INPUT,
            )

    def protect_using_old_api(self, requested_configuration, project_and_group, branch):
        warning(
            f"Using keys {self.old_api_keys} for configuring protected"
            " branches is deprecated and will be removed in future versions of GitLabForm."
            f" Please start using new keys: {self.new_api_keys}"
        )
        debug("Setting branch '%s' as *protected*", branch)

        # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)

        self.gitlab.protect_branch(
            project_and_group,
            branch,
            requested_configuration["developers_can_push"],
            requested_configuration["developers_can_merge"],
        )

    def protect_using_new_api(self, requested_configuration, project_and_group, branch):
        debug("Setting branch '%s' access level", branch)

        # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)

        protect_rules = {
            key: value
            for key, value in requested_configuration.items()
            if key != "protected"
        }

        self.gitlab.branch_access_level(
            project_and_group,
            branch,
            protect_rules,
        )

    def set_code_owner_approval_required(
        self, requested_configuration, project_and_group, branch
    ):
        debug(
            "Setting branch '%s' \"code owner approval required\" option",
            branch,
        )
        self.gitlab.branch_code_owner_approval_required(
            project_and_group,
            branch,
            requested_configuration["code_owner_approval_required"],
        )

    def configuration_update_needed(
        self, requested_configuration, project_and_group, branch
    ):
        try:
            result = self.gitlab.get_branch_access_levels(project_and_group, branch)
        except NotFoundException:
            return True

        if "push_access_levels" in result and len(result["push_access_levels"]) == 1:
            current_push_access_level = result["push_access_levels"][0]["access_level"]
        if "merge_access_levels" in result and len(result["merge_access_levels"]) == 1:
            current_merge_access_level = result["merge_access_levels"][0][
                "access_level"
            ]
        if (
            "unprotect_access_levels" in result
            and len(result["unprotect_access_levels"]) == 1
        ):
            current_unprotect_access_level = result["unprotect_access_levels"][0][
                "access_level"
            ]

        requested_push_access_level = requested_configuration.get("push_access_level")
        requested_merge_access_level = requested_configuration.get("merge_access_level")
        requested_unprotect_access_level = requested_configuration.get(
            "unprotect_access_level"
        )

        access_levels_are_different = (
            requested_push_access_level,
            requested_merge_access_level,
            requested_unprotect_access_level,
        ) != (
            current_push_access_level,
            current_merge_access_level,
            current_unprotect_access_level,
        )

        if access_levels_are_different:
            return True

        # after checking the levels, we check the rest of the parameters
        extra_params = [
            extra_param
            for extra_param in requested_configuration.keys()
            if extra_param != "protected"
            and extra_param not in self.old_api_keys
            and extra_param not in self.new_api_keys
        ]

        for param in extra_params:
            if result[param] != requested_configuration[param]:
                return True

        return False

    def unprotect(self, project_and_group, branch):
        debug("Setting branch '%s' as unprotected", branch)
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)
