from typing import Dict

from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.badges_processor import BadgesProcessor


class ProjectBadgesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("badges", gitlab)
        self._badges_processor = BadgesProcessor()

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_badges: Dict = configuration.get("badges", {})
        enforce = configured_badges.pop("enforce", False)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        self._badges_processor.process_badges(
            self.configuration_name,
            configured_badges,
            enforce,
            project,
            self._needs_update,
        )
