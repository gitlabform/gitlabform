from cli_ui import fatal, debug
from typing import Callable
from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


class MergeRequestsApprovals(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("merge_requests_approvals", gitlab)
        self.get_entity_in_gitlab: Callable = getattr(self, "get_project_mr_approvals_settings")

    def _process_configuration(self, project_path: str, configuration: dict) -> None:
        debug("Processing project merge requests approvals settings...")
        project: Project = self.gl.get_project_by_path_cached(project_path)

        mr_approval_settings_in_config: dict = configuration.get("merge_requests_approvals", {})
        mr_approval_settings_in_gitlab: dict = project.approvals.get().asdict()

        debug(mr_approval_settings_in_gitlab)
        debug("merge_requests_approvals BEFORE: ^^^")

        if self._needs_update(mr_approval_settings_in_gitlab, mr_approval_settings_in_config):
            debug("Updating project merge requests approvals settings")
            project.approvals.update(**mr_approval_settings_in_config)

            debug(project.approvals.get().asdict())
            debug("merge_requests_approvals AFTER: ^^^")
        else:
            debug("No update needed for project merge requests approvals settings")

    def get_project_mr_approvals_settings(self, project_path: str):
        return self.gl.get_project_by_path_cached(project_path).approvals.get().asdict()

    def _can_proceed(self, project_or_group: str, configuration: dict):
        if "approvals_before_merge" in configuration["merge_requests_approvals"]:
            fatal(
                "Setting the 'approvals_before_merge' in the 'merge_requests_approvals' sections is not allowed "
                "as it is not clear which rule does it apply to. "
                "Please set it inside the specific approval rules in the 'merge_requests_approval_rules' section."
            )
        else:
            return True

    # TODO: duplicated logic with project_settings_processor.py. Should be refactored - ideally in the AbstractProcessor
    def _print_diff(self, project_or_project_and_group: str, entity_config, diff_only_changed: bool):
        entity_in_gitlab = self.get_project_mr_approvals_settings(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )
