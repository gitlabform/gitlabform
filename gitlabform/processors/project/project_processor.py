from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ProjectProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project = configuration["project"]
        if project:
            if "archive" in project:
                if project["archive"]:
                    verbose("Archiving project...")
                    self.gitlab.archive(project_and_group)
                else:
                    verbose("Unarchiving project...")
                    self.gitlab.unarchive(project_and_group)
