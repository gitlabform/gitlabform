import logging
from abc import ABC, abstractmethod

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
                logging.info(
                    "Skipping %s - explicitly configured to do so."
                    % self.__configuration_name
                )
            elif dry_run:
                logging.info(
                    "Processing %s in dry-run mode." % self.__configuration_name
                )
                self._log_changes(
                    project_or_project_and_group,
                    configuration.get(self.__configuration_name),
                )
            else:
                logging.info("Processing %s" % self.__configuration_name)
                self._process_configuration(project_or_project_and_group, configuration)
        else:
            logging.debug("Skipping %s - not in config." % self.__configuration_name)

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _log_changes(self, project_or_project_and_group: str, configuration_to_process):
        logging.info(
            "Diffing for %s section is not supported yet" % self.__configuration_name
        )
