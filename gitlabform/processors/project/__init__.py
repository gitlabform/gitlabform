from typing import List

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessors
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.project.badges_processor import BadgesProcessor
from gitlabform.processors.project.branches_processor import (
    BranchesProcessor,
)
from gitlabform.processors.project.deploy_keys_processor import (
    DeployKeysProcessor,
)
from gitlabform.processors.project.files_processor import FilesProcessor
from gitlabform.processors.project.hooks_processor import HooksProcessor
from gitlabform.processors.project.members_processor import MembersProcessor
from gitlabform.processors.project.merge_requests_processor import (
    MergeRequestsProcessor,
)
from gitlabform.processors.project.project_processor import ProjectProcessor
from gitlabform.processors.project.project_push_rules_processor import (
    ProjectPushRulesProcessor,
)
from gitlabform.processors.project.project_settings_processor import (
    ProjectSettingsProcessor,
)
from gitlabform.processors.project.schedules_processor import (
    SchedulesProcessor,
)
from gitlabform.processors.project.variables_processor import (
    VariablesProcessor,
)
from gitlabform.processors.project.integrations_processor import (
    IntegrationsProcessor,
)
from gitlabform.processors.project.tags_processor import TagsProcessor


class ProjectProcessors(AbstractProcessors):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__(gitlab, config, strict)
        self.processors: List[AbstractProcessor] = [
            ProjectProcessor(gitlab),
            ProjectSettingsProcessor(gitlab),
            ProjectPushRulesProcessor(gitlab),
            MergeRequestsProcessor(gitlab),
            DeployKeysProcessor(gitlab),
            VariablesProcessor(gitlab),
            BranchesProcessor(gitlab, strict),
            TagsProcessor(gitlab, strict),
            IntegrationsProcessor(gitlab),
            FilesProcessor(gitlab, config, strict),
            HooksProcessor(gitlab),
            MembersProcessor(gitlab),
            SchedulesProcessor(gitlab),
            BadgesProcessor(gitlab),
        ]
