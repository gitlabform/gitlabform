from abc import ABC

import requests
from cli_ui import debug as verbose

from typing import List

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfigurationFile
from gitlabform.processors.abstract_processor import AbstractProcessor


class AbstractProcessors(ABC):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        self.processors: List[AbstractProcessor] = []

    def get_configuration_names(self):
        return [processor.configuration_name for processor in self.processors]

    def process_entity(
        self,
        entity_reference: str,
        configuration: dict,
        dry_run: bool,
        diff_only_changed: bool,
        effective_configuration: EffectiveConfigurationFile,
        only_sections: List[str],
    ):
        for processor in self.processors:
            if only_sections == "all" or processor.configuration_name in only_sections:
                processor.process(
                    entity_reference, configuration, dry_run, diff_only_changed, effective_configuration
                )
            else:
                verbose(
                    f"Skipping section '{processor.configuration_name}' - not in --only-sections list."
                )
