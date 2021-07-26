from typing import List, Optional, TextIO

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
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
from gitlabform.processors.project.secret_variables_processor import (
    SecretVariablesProcessor,
)
from gitlabform.processors.project.services_processor import (
    ServicesProcessor,
)
from gitlabform.processors.project.tags_processor import TagsProcessor


class ProjectProcessors(object):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        self.processors: List[AbstractProcessor] = [
            ProjectProcessor(gitlab),
            ProjectSettingsProcessor(gitlab),
            ProjectPushRulesProcessor(gitlab),
            MergeRequestsProcessor(gitlab),
            DeployKeysProcessor(gitlab),
            SecretVariablesProcessor(gitlab),
            BranchesProcessor(gitlab, strict),
            TagsProcessor(gitlab, strict),
            ServicesProcessor(gitlab),
            FilesProcessor(gitlab, config, strict),
            HooksProcessor(gitlab),
            MembersProcessor(gitlab),
            SchedulesProcessor(gitlab),
        ]

    def process_project(
        self,
        project_and_group: str,
        configuration: dict,
        dry_run: bool,
        output_file: Optional[TextIO],
    ):
        for processor in self.processors:
            processor.process(project_and_group, configuration, dry_run, output_file)
