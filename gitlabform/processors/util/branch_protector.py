from logging import debug
from cli_ui import warning, fatal

from gitlabform.constants import EXIT_PROCESSING_ERROR, EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException


class BranchProtector:
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

            self.validate_branch_protection_config(
                project_and_group, requested_configuration, branch
            )

            if any(
                extra_key in requested_configuration
                for extra_key in self.extra_param_keys
            ):
                for extra_param_key in self.extra_param_keys:
                    # check if an extra_param is in config, and it contains the user parameter
                    if extra_param_key in requested_configuration and any(
                        "user" in d for d in requested_configuration[extra_param_key]
                    ):
                        for extra_config in requested_configuration[extra_param_key]:
                            # loop over the array of extra param and get the user_id related to user
                            if "user" in extra_config.keys():
                                user_id = self.gitlab._get_user_id(
                                    extra_config.pop("user")
                                )
                                extra_config["user_id"] = user_id

            if self.configuration_update_needed(
                requested_configuration, project_and_group, branch
            ):
                self.do_protect_branch(
                    requested_configuration, project_and_group, branch
                )
            else:
                debug(
                    "Skipping setting branch '%s' protection configuration because it's already as requested.",
                    branch,
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
            self.gitlab.unprotect_branch(project_and_group, branch)

        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def validate_branch_protection_config(
        self, project_and_group, requested_configuration, branch
    ):
        # for the new API any key needs to be defined...
        if any(
            key in requested_configuration
            for key in self.new_api_keys + self.extra_param_keys
        ):
            return
        else:
            fatal(
                f"Invalid configuration for protecting branches in project '{project_and_group}',"
                f" branch '{branch}' - missing keys. Required is any of these: "
                f"{self.new_api_keys + self.extra_param_keys}",
                exit_code=EXIT_INVALID_INPUT,
            )

    def do_protect_branch(self, requested_configuration, project_and_group, branch):
        debug("Setting branch '%s' access level", branch)

        # Protected Branches API is one of those that do not support editing entities
        # (PUT is not documented for it, at least). so you need to delete existing
        # branch protection (DELETE) and recreate it (POST) to perform an update
        # (otherwise you get HTTP 409 "Protected branch 'foo' already exists")
        self.gitlab.unprotect_branch(project_and_group, branch)

        # replace in our config our custom "user" and "group" entries with supported by
        # the Protected Branches API "user_id" and "group_id"
        for extra_param_key in self.extra_param_keys:
            for element in requested_configuration.get(extra_param_key, []):
                if "user" in element.keys():
                    user_id = self.gitlab._get_user_id(element.pop("user"))
                    element["user_id"] = user_id
                elif "group" in element.keys():
                    group_id = self.gitlab._get_group_id(element.pop("group"))
                    element["group_id"] = group_id

        protect_rules = {
            key: value
            for key, value in requested_configuration.items()
            if key != "protected"
        }

        self.gitlab.protect_branch(
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
        self.gitlab.set_branch_code_owner_approval_required(
            project_and_group,
            branch,
            requested_configuration["code_owner_approval_required"],
        )

    def configuration_update_needed(
        self, requested_configuration, project_and_group, branch
    ):
        # get current configuration of branch access level
        current = self.get_current_branch_configuration(project_and_group, branch)

        # get requested configuration of branch access level
        requested = self.get_requested_branch_configuration(requested_configuration)

        debug("Current branch '%s' access levels: %s", branch, current)
        debug("Requested branch '%s' access levels: %s", branch, requested)
        return current != requested

    def get_current_branch_configuration(self, project_and_group_name, branch):
        # from a response for a request to Protected Branches API GET request
        # (https://docs.gitlab.com/ee/api/protected_branches.html#get-a-single-protected-branch-or-wildcard-protected-branch)
        # like:
        #
        # {
        #     "id": 1,
        #     "name": "master",
        #     "push_access_levels": [
        #         {
        #             "access_level": 40,
        #             "access_level_description": "Maintainers"
        #         }
        #     ],
        #     "merge_access_levels": [
        #         {
        #             "access_level": 40,
        #             "access_level_description": "Maintainers"
        #         }
        #     ],
        #     "allow_force_push":false,
        #     "code_owner_approval_required": false
        # }
        #
        # ...gets flat tuple of the permissions to perform each kind of 3 actions (push/merge/unprotect) and
        # the other extra settings that can be applied using Protected Branches API POST request
        #
        try:
            protected_branches_response = self.gitlab.get_branch_access_levels(
                project_and_group_name, branch
            )

            return (
                *(
                    self.get_current_permissions(protected_branches_response, "push")
                ),  # tuple of 3
                *(
                    self.get_current_permissions(protected_branches_response, "merge")
                ),  # tuple of 3
                *(
                    self.get_current_permissions(
                        protected_branches_response, "unprotect"
                    )
                ),  # tuple of 3
                protected_branches_response.get("allow_force_push"),
                # code_owner_approval_required has to use PATCH request, see set_code_owner_approval_required()
            )
        except NotFoundException:
            return tuple([None] * 10)  # = 3 * 3 + 1

    def get_current_permissions(self, protected_branches_response, action):
        # from a response for a request to Protected Branches API GET request
        # (https://docs.gitlab.com/ee/api/protected_branches.html#get-a-single-protected-branch-or-wildcard-protected-branch)
        # like:
        #
        # {
        #     "id": 1,
        #     "name": "master",
        #     "push_access_levels": [
        #         {
        #             "access_level": 40,
        #             "access_level_description": "Maintainers"
        #         }
        #     ],
        #     "merge_access_levels": [
        #         {
        #             "access_level": 40,
        #             "access_level_description": "Maintainers"
        #         }
        #     ],
        #     "allow_force_push":false,
        #     "code_owner_approval_required": false
        # }
        #
        # ...gets a tuple of sorted lists, for a given permission in ["push", "merge", "unprotect"],
        # for example for "push":
        #
        # ([40], [], [])
        #

        levels = set()
        user_ids = set()
        group_ids = set()
        # we ignore the description

        # we use the safe .get() everywhere below as those elements may not exist
        for array_element in protected_branches_response.get(
            f"{action}_access_levels", []
        ):
            if array_element.get("access_level") is not None:
                levels.add(array_element.get("access_level"))
            elif array_element.get("user_id"):
                user_ids.add(array_element.get("user_id"))
            elif array_element.get("group_id"):
                group_ids.add(array_element.get("group_id"))

        return sorted(levels), sorted(user_ids), sorted(group_ids)

    def get_requested_branch_configuration(self, requested_configuration):
        # from a configuration entry like:
        #
        #   # Allow specific users to push and merge to this branch - *** this syntax requires GitLab Premium (paid) ***
        #   protected: true
        #   allowed_to_push:
        #     - user: jsmith # you can use usernames...
        #     - user: bdoe
        #   allowed_to_merge:
        #     - user_id: 15 # ...or user ids, if you know them
        #
        # ...gets a flat tuple exactly like get_current_branch_protection_settings(), so they can be compared.
        #

        return (
            *(
                self.get_requested_permissions(requested_configuration, "push")
            ),  # tuple of 3
            *(
                self.get_requested_permissions(requested_configuration, "merge")
            ),  # tuple of 3
            *(
                self.get_requested_permissions(requested_configuration, "unprotect")
            ),  # tuple of 3
            requested_configuration.get("allow_force_push", False),
            # code_owner_approval_required has to use PATCH request, see set_code_owner_approval_required()
        )

    def get_requested_permissions(self, requested_configuration, action):
        # from a configuration entry like:
        #
        #   protected: true
        #   allowed_to_push:
        #     - user: jsmith # you can use usernames...
        #     - user: bdoe
        #   allowed_to_merge:
        #     - user_id: 15 # ...or user ids, if you know them
        #
        # ...gets a tuple of sorted lists of entities (levels, users, groups) having the permissions
        # to do the specific action (push/merge/unprotect).
        #
        # for example for "push" action for the config above the return value would be:
        #
        # ([], [123, 456], [])
        #
        # ...where 123, 456 are ids of users jsmith and bdoe

        levels = set()
        user_ids = set()
        group_ids = set()
        # we ignore the description

        if f"{action}_access_level" in requested_configuration:
            levels.add(requested_configuration.get(f"{action}_access_level"))

        if f"allowed_to_{action}" in requested_configuration:
            for config in requested_configuration[f"allowed_to_{action}"]:
                if "access_level" in config:
                    levels.add(config["access_level"])
                elif "user_id" in config:
                    user_ids.add(config["user_id"])
                elif "user" in config:
                    user_ids.add(self.gitlab._get_user_id(config["user"]))
                elif "group_id" in config:
                    group_ids.add(config["group_id"])
                elif "group" in config:
                    group_ids.add(self.gitlab._get_group_id(config["group"]))

        return sorted(levels), sorted(user_ids), sorted(group_ids)
