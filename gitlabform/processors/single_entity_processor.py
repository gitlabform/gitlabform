from logging import debug
from cli_ui import debug as verbose

import abc
from typing import Callable, Optional

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


def noop():
    pass


class SingleEntityProcessor(AbstractProcessor, metaclass=abc.ABCMeta):
    def __init__(
        self,
        configuration_name: str,
        gitlab: GitLab,
        get_method_name: str,
        edit_method_name: str,
        add_method_name: Optional[str] = None,
    ):
        super().__init__(configuration_name, gitlab)
        self.get_method: Callable = getattr(self.gitlab, get_method_name)
        self.edit_method: Callable = getattr(self.gitlab, edit_method_name)
        if add_method_name:
            self.add_method: Callable = getattr(self.gitlab, add_method_name)
        else:
            self.add_method = noop

    def _process_configuration(self, project_or_group: str, configuration: dict):

        entity_config = configuration[self.configuration_name]

        entity_in_gitlab = self.get_method(project_or_group)
        debug(f"{self.configuration_name} BEFORE: ^^^")

        if entity_in_gitlab:
            if self._needs_update(entity_in_gitlab, entity_config):
                verbose(f"Editing {self.configuration_name} in {project_or_group}")
                self.edit_method(project_or_group, entity_config)
                debug(f"{self.configuration_name} AFTER: ^^^")
            else:
                verbose(
                    f"{self.configuration_name} in {project_or_group} doesn't need an update."
                )
        else:
            verbose(f"Adding {self.configuration_name} in {project_or_group}")
            self.add_method(project_or_group, entity_config)
            debug(f"{self.configuration_name} AFTER: ^^^")

    def _print_diff(self, project_or_project_and_group: str, entity_config):

        entity_in_gitlab = self.get_method(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
        )
