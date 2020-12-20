import logging
from abc import ABC, abstractmethod
from functools import wraps

from gitlabform.common.safe_dict import SafeDict


def configuration_to_safe_dict(method):
    """
    This wrapper function calls the method with the configuration converted from a regular dict into a SafeDict
    """

    @wraps(method)
    def method_wrapper(self, project_and_group, configuration, dry_run):
        return method(self, project_and_group, SafeDict(configuration), dry_run)

    return method_wrapper


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
