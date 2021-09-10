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
    extra_param_keys = [
        "allowed_to_push",
        "allowed_to_merge",
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
                # when congiguration contains at least one of  allowed_to_push and allowed_to_merge
                if any(
                    extra_key in requested_configuration
                    for extra_key in self.extra_param_keys
                ):
                    for extra_param_key in self.extra_param_keys:
                        # check if an extra_param is in config and it contain user parameter
                        if extra_param_key in requested_configuration and any(
                            "user" in d
                            for d in requested_configuration[extra_param_key]
                        ):
                            for extra_config in requested_configuration[
                                extra_param_key
                            ]:
                                # loop over the array of extra param and get the user_id related to user
                                if "user" in extra_config.keys():
                                    user_id = self.gitlab.get_user_to_protect_branch(
                                        extra_config.pop("user")
                                    )
                                    extra_config["user_id"] = user_id

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
        # get current configuration of branch access level
        (
            current_push_access_levels,  # push access level array only
            current_merge_access_levels,  # merge access level array only
            current_push_access_user_ids,  # push allowed user array
            current_merge_access_user_ids,  # merge allowed user array
            current_unprotect_access_level,
        ) = self.gitlab.get_only_branch_access_levels(project_and_group, branch)

        requested_push_access_levels = [
            requested_configuration.get("push_access_level")
        ]
        requested_push_access_user_ids = []
        if "allowed_to_push" in requested_configuration:
            for config in requested_configuration["allowed_to_push"]:
                if "access_level" in config:
                    # complete push access level arrays with the allowed_to_push array if access_level is defined
                    requested_push_access_levels.append(config["access_level"])
                elif "user_id" in config:
                    # complete push allowed user arrays with the allowed_to_push array data if user_id is defined
                    requested_push_access_user_ids.append(config["user_id"])
                elif "user" in config:
                    # complete push allowed user arrays with the allowed_to_push array data if user is defined
                    requested_push_access_user_ids.append(
                        self.gitlab.get_user_to_protect_branch(config["user"])
                    )

        requested_push_access_levels.sort()
        requested_push_access_user_ids.sort()

        requested_merge_access_levels = [
            requested_configuration.get("merge_access_level")
        ]
        requested_merge_access_user_ids = []
        if "allowed_to_merge" in requested_configuration:
            for config in requested_configuration["allowed_to_merge"]:
                if "access_level" in config:
                    # complete merge access level arrays with the allowed_to_push array if access_level is defined
                    requested_merge_access_levels.append(config["access_level"])
                elif "user_id" in config:
                    # complete merge allowed user arrays with the allowed_to_push array data if user_id is defined
                    requested_merge_access_user_ids.append(config["user_id"])
                elif "user" in config:
                    # complete merge allowed user arrays with the allowed_to_push array data if user is defined
                    requested_merge_access_user_ids.append(
                        self.gitlab.get_user_to_protect_branch(config["user"])
                    )

        requested_merge_access_levels.sort()
        requested_merge_access_user_ids.sort()

        requested_unprotect_access_level = requested_configuration.get(
            "unprotect_access_level"
        )

        access_levels_are_different = (
            requested_push_access_levels,
            requested_merge_access_levels,
            requested_push_access_user_ids,
            requested_merge_access_user_ids,
            requested_unprotect_access_level,
        ) != (
            current_push_access_levels,
            current_merge_access_levels,
            current_push_access_user_ids,
            current_merge_access_user_ids,
            current_unprotect_access_level,
        )

        if access_levels_are_different:
            return True

        return False

    def unprotect(self, project_and_group, branch):
        debug("Setting branch '%s' as unprotected", branch)
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)
