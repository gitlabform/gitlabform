from typing import Dict

from gitlab.v4.objects import Group

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.badges_processor import BadgesProcessor


class GroupBadgesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_badges", gitlab)
        self._badges_processor = BadgesProcessor()

    def _process_configuration(self, group_path_and_name: str, configuration: Dict):
        configured_badges: Dict = configuration.get("group_badges", {})
        enforce = configured_badges.pop("enforce", False)

        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)

        self._badges_processor.process_badges(
            self.configuration_name,
            configured_badges,
            enforce,
            group,
            self._needs_update,
        )
