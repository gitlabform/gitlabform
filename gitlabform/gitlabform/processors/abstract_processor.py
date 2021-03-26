import logging
from abc import ABC, abstractmethod

import cli_ui

from gitlabform.gitlabform.processors.util.decorators import configuration_to_safe_dict


class AbstractProcessor(ABC):
    def __init__(self, configuration_name):
        self.__configuration_name = configuration_name

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration: dict,
        dry_run: bool = False,
    ):
        if self.__configuration_name in configuration:
            if configuration.get(self.__configuration_name + "|skip"):
                cli_ui.debug(
                    f"Skipping {self.__configuration_name} - explicitly configured to do so."
                )
            elif dry_run:
                cli_ui.debug(f"Processing {self.__configuration_name} in dry-run mode.")
                self._log_changes(
                    project_or_project_and_group,
                    configuration.get(self.__configuration_name),
                )
            elif (
                configuration.get("project|archive")
                and self.__configuration_name != "project"
            ):
                cli_ui.debug(
                    f"Skipping {self.__configuration_name} - it is configured to be archived."
                )
            else:
                cli_ui.debug(f"Processing {self.__configuration_name}")
                self._process_configuration(project_or_project_and_group, configuration)
        else:
            logging.debug("Skipping %s - not in config." % self.__configuration_name)

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _log_changes(self, project_or_project_and_group: str, configuration_to_process):
        cli_ui.debug(
            f"Diffing for {self.__configuration_name} section is not supported yet"
        )
