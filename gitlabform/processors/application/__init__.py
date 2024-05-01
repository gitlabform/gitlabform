from typing import List

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessors
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.application.application_settings_processor import (
    ApplicationSettingsProcessor,
)


class ApplicationProcessors(AbstractProcessors):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__(gitlab, config, strict)
        self.processors: List[AbstractProcessor] = [
            ApplicationSettingsProcessor(gitlab),
        ]
