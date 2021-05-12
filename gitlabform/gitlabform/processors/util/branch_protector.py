import logging
import sys

import cli_ui

from gitlabform import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException


class BranchProtector(object):
    def __init__(self, gitlab: GitLab, strict: bool):
        self.gitlab = gitlab
        self.strict = strict

    def protect_branch(self, project_and_group, configuration, branch):
        try:
            if (
                "protected" in configuration["branches"][branch]
                and configuration["branches"][branch]["protected"]
            ):
                if ("developers_can_push" and "developers_can_merge") in configuration[
                    "branches"
                ][branch]:
                    logging.debug("Setting branch '%s' as *protected*", branch)
                    # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
                    self.gitlab.unprotect_branch_new_api(project_and_group, branch)
                    self.gitlab.protect_branch(
                        project_and_group,
                        branch,
                        configuration["branches"][branch]["developers_can_push"],
                        configuration["branches"][branch]["developers_can_merge"],
                    )
                elif (
                    "push_access_level"
                    and "merge_access_level"
                    and "unprotect_access_level"
                ) in configuration["branches"][branch]:
                    try:
                        branch_access_levels = self.gitlab.get_branch_access_levels(project_and_group, branch)
                        levels = ["push_access_levels", "merge_access_levels", "unprotect_access_levels"]
                        # Check each access type has the correct access level, if they do, not change is needed
                        # Gitlabform uses access_levels with plural form, and gitlab uses singular form.
                        # [0:-1] removes the plural
                        if all(configuration["branches"][branch][level[0:-1]] == branch_access_levels[level][0]["access_level"] for level in levels):
                            logging.debug("Skipping set branch '%s' access levels because they're already set")
                            return

                    except NotFoundException:
                        logging.debug("No access levels for this branch exist yet")

                    logging.debug("Setting branch '%s' access level", branch)
                    # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
                    self.gitlab.unprotect_branch_new_api(project_and_group, branch)
                    self.gitlab.branch_access_level(
                        project_and_group,
                        branch,
                        configuration["branches"][branch]["push_access_level"],
                        configuration["branches"][branch]["merge_access_level"],
                        configuration["branches"][branch]["unprotect_access_level"],
                    )
                if "code_owner_approval_required" in configuration["branches"][branch]:
                    logging.debug(
                        "Setting branch '%s' \"code owner approval required\" option",
                        branch,
                    )
                    self.gitlab.branch_code_owner_approval_required(
                        project_and_group,
                        branch,
                        configuration["branches"][branch][
                            "code_owner_approval_required"
                        ],
                    )
            else:
                logging.debug("Setting branch '%s' as unprotected", branch)
                self.gitlab.unprotect_branch_new_api(project_and_group, branch)
        except NotFoundException:
            message = f"Branch '{branch}' not found when trying to set it as protected/unprotected!"
            if self.strict:
                cli_ui.error(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                cli_ui.warning(message)
