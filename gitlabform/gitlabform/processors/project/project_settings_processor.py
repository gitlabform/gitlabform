import logging

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.gitlabform.processors.util.difference_logger import DifferenceLogger


class ProjectSettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_settings")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project_settings = configuration["project_settings"]
        logging.debug(
            "Project settings BEFORE: %s",
            self.gitlab.get_project_settings(project_and_group),
        )
        logging.info("Setting project settings: %s", project_settings)
        self.gitlab.put_project_settings(project_and_group, project_settings)
        logging.debug(
            "Project settings AFTER: %s",
            self.gitlab.get_project_settings(project_and_group),
        )

    def _log_changes(self, project_and_group: str, project_settings):
        current_project_settings = self.gitlab.get_project_settings(project_and_group)
        DifferenceLogger.log_diff(
            "Project %s changes" % project_and_group,
            current_project_settings,
            project_settings,
        )
