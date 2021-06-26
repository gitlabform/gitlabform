import logging

import cli_ui

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
                    cli_ui.debug("Archiving project...")
                    self.gitlab.archive(project_and_group)
                else:
                    cli_ui.debug("Unarchiving project...")
                    self.gitlab.unarchive(project_and_group)
