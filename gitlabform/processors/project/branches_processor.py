from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.branch_protector import BranchProtector
from cli_ui import debug as verbose, warning
import time


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.__branch_protector = BranchProtector(gitlab, strict)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for branch in sorted(configuration["branches"]):
            if "members" in configuration:
                # When gitlabform needs to update project membership and also
                # configure branch protection, there seems to be a race condition
                # or delay in GitLab. Automated acceptance tests in gitlabform
                # creates new user and adds to the project followed by configuring
                # branch protection setting. In that scenario need to wait a little
                # before calling GitLab's REST API for branch protection. Otherwise
                # the API returns error code 422 with an message like "Push access
                # levels user is not a member of the project"

                time.sleep(2)

            self.__branch_protector.apply_branch_protection_configuration(
                project_and_group, configuration, branch
            )
