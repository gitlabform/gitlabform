import sys
from logging import debug, info, critical
from gitlab.v4.objects import Project

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class MergeRequestsApprovals(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("merge_requests_approvals", gitlab)

    def _get_entities_for_diff(self, project_path: str, entity_config: dict) -> tuple[dict, dict]:
        return self.gl.get_project_by_path_cached(project_path).approvals.get().asdict(), entity_config

    def _process_configuration(self, project_path: str, configuration: dict) -> None:
        info("Processing project merge requests approvals settings...")
        project: Project = self.gl.get_project_by_path_cached(project_path)

        mr_approval_settings_in_config: dict = configuration.get("merge_requests_approvals", {})
        mr_approval_settings_in_gitlab: dict = project.approvals.get().asdict()

        info(mr_approval_settings_in_gitlab)
        info("merge_requests_approvals BEFORE: ^^^")

        if self._needs_update(mr_approval_settings_in_gitlab, mr_approval_settings_in_config):
            debug("Updating project merge requests approvals settings")
            project.approvals.update(**mr_approval_settings_in_config)

            info(project.approvals.get().asdict())
            info("merge_requests_approvals AFTER: ^^^")
        else:
            info("No update needed for project merge requests approvals settings")

    def _can_proceed(self, project_or_group: str, configuration: dict):
        if "approvals_before_merge" in configuration["merge_requests_approvals"]:
            critical(
                "Setting the 'approvals_before_merge' in the 'merge_requests_approvals' sections is not allowed "
                "as it is not clear which rule does it apply to. "
                "Please set it inside the specific approval rules in the 'merge_requests_approval_rules' section."
            )
            sys.exit(EXIT_INVALID_INPUT)
        else:
            return True
