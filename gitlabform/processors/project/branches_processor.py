from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.branch_protector import BranchProtector


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.__branch_protector = BranchProtector(gitlab, strict)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for branch in sorted(configuration["branches"]):
            self.__branch_protector.apply_branch_protection_configuration(
                project_and_group, configuration, branch
            )
