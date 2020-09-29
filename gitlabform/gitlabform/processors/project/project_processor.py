import logging

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class ProjectProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project")
        self.gitlab = gitlab

    def _process_configuration(
        self, project_and_group: str, configuration: dict, do_apply: bool = True
    ):
        project = configuration["project"]
        if project:
            if "archive" in project:
                if project["archive"]:
                    logging.info("Archiving project...")
                    self.gitlab.archive(project_and_group)
                else:
                    logging.info("Unarchiving project...")
                    self.gitlab.unarchive(project_and_group)

    def _log_changes(self, project_and_group: str, project):
        logging.info("Diffing for project section is not supported yet")
