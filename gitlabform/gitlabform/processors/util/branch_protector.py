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

            if requested_configuration.get("protected"):

                # note that for old API *all* keys have to be defined...
                if all(key in requested_configuration for key in self.old_api_keys):

                    # unprotect first to reset 'allowed to merge' and 'allowed to push' fields

                    self.protect_using_old_api(
                        requested_configuration, project_and_group, branch
                    )

                # ...while for the new one we need ANY new key
                elif any(key in requested_configuration for key in self.new_api_keys):

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
            requested_configuration.get("push_access_level", None),
            requested_configuration.get("merge_access_level", None),
            requested_configuration.get("unprotect_access_level", None),
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

        requested_push_access_level = requested_configuration.get("push_access_level")
        requested_merge_access_level = requested_configuration.get("merge_access_level")
        requested_unprotect_access_level = requested_configuration.get(
            "unprotect_access_level"
        )

        (
            current_push_access_level,
            current_merge_access_level,
            current_unprotect_access_level,
        ) = self.gitlab.get_only_branch_access_levels(project_and_group, branch)

        return (
            requested_push_access_level,
            requested_merge_access_level,
            requested_unprotect_access_level,
        ) != (
            current_push_access_level,
            current_merge_access_level,
            current_unprotect_access_level,
        )

    def unprotect(self, project_and_group, branch):
        logging.debug("Setting branch '%s' as unprotected", branch)
        self.gitlab.unprotect_branch_new_api(project_and_group, branch)
