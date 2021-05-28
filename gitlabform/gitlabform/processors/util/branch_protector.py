import logging
import sys

import cli_ui

from gitlabform import EXIT_PROCESSING_ERROR
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

    def protect_branch(self, project_and_group, configuration, branch):
        try:
            requested_configuration = configuration["branches"][branch]

            if (
                "protected" in requested_configuration
                and requested_configuration["protected"]
            ):

                if all(key in requested_configuration for key in self.old_api_keys):

                    # unprotect first to reset 'allowed to merge' and 'allowed to push' fields

                    self.protect_using_old_api(
                        requested_configuration, project_and_group, branch
                    )

                elif all(key in requested_configuration for key in self.new_api_keys):

                    if self.configuration_update_needed(
                        requested_configuration, project_and_group, branch
                    ):
                        self.protect_using_new_api(
                            requested_configuration, project_and_group, branch
                        )
                    else:
                        logging.debug(
                            "Skipping set branch '%s' access levels because they're already set"
                        )
                        return
                        # TODO: is this ok that we skip below code in this case?

                if "code_owner_approval_required" in requested_configuration:

                    self.set_code_owner_approval_required(
                        requested_configuration, project_and_group, branch
                    )

            else:

                self.unprotect(project_and_group, branch)

        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                cli_ui.error(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                cli_ui.warning(message)

    def protect_using_old_api(self, requested_configuration, project_and_group, branch):
        logging.warning(
            f"Using keys {self.old_api_keys} for configuring protected"
            " branches is deprecated and will be removed in future versions of GitLabForm."
            f" Please start using new keys: {self.new_api_keys}"
        )
        logging.debug("Setting branch '%s' as *protected*", branch)

        # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)

        self.gitlab.protect_branch(
            project_and_group,
            branch,
            requested_configuration["developers_can_push"],
            requested_configuration["developers_can_merge"],
        )

    def protect_using_new_api(self, requested_configuration, project_and_group, branch):
        logging.debug("Setting branch '%s' access level", branch)

        # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)

        self.gitlab.branch_access_level(
            project_and_group,
            branch,
            requested_configuration["push_access_level"],
            requested_configuration["merge_access_level"],
            requested_configuration["unprotect_access_level"],
        )

    def set_code_owner_approval_required(
        self, requested_configuration, project_and_group, branch
    ):
        logging.debug(
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
        levels = [
            "push_access_levels",
            "merge_access_levels",
            "unprotect_access_levels",
        ]

        # In GitLab API level names are plural, while in our config syntax we require singular.
        # Let's convert our config to the same form as GitLab's to make the further processing easier.

        requested_configuration_in_plural = {}
        for level in levels:
            requested_configuration_in_plural[level] = requested_configuration[
                level[0:-1]
            ]

        try:
            current_configuration = self.gitlab.get_branch_access_levels(
                project_and_group, branch
            )

            # Example output:

            # {'id': 4, 'name': 'main',
            # 'push_access_levels':
            # [{'access_level': 40, 'access_level_description': 'Maintainers', 'user_id': None, 'group_id': None}],
            # 'merge_access_levels':
            # [{'access_level': 40, 'access_level_description': 'Maintainers', 'user_id': None, 'group_id': None}],
            # 'unprotect_access_levels':
            # [],
            # 'code_owner_approval_required': False, 'allow_force_push': False, }

        except NotFoundException:
            logging.debug("No access levels for this branch exist yet")
            return True

        # The only type of new API configuration that we support is when all 3 levels are defined as a single value
        # (level).

        # So if any of the levels is not present in the current configuration from GitLab
        # or it is something else than a single-element array (single level), then the configs are different.
        if any(
            level not in current_configuration or len(current_configuration[level]) != 1
            for level in levels
        ):
            return True

        # If any of the requested access level does not match the level defined GitLab, then the configs are different.

        # (The [0] is for getting that single element - single level - from an array.)
        if any(
            requested_configuration_in_plural[level]
            != current_configuration[level][0]["access_level"]
            for level in levels
        ):
            return True

        return False

    def unprotect(self, project_and_group, branch):
        logging.debug("Setting branch '%s' as unprotected", branch)
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)
