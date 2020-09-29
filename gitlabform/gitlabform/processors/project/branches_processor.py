import logging

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.gitlabform.processors.util.branch_protector import BranchProtector


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches")
        self.__branch_protector = BranchProtector(gitlab, strict)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for branch in sorted(configuration["branches"]):
            self.__branch_protector.protect_branch(
                project_and_group, configuration, branch
            )

    def _log_changes(self, project_and_group: str, branches):
        logging.info("Diffing for branches section is not supported yet")
