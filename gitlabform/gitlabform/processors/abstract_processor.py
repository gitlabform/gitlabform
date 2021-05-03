import logging
import textwrap
from typing import Optional, TextIO
from abc import ABC, abstractmethod

import cli_ui
import yaml

from gitlabform.gitlabform.processors.util.decorators import configuration_to_safe_dict


class AbstractProcessor(ABC):
    def __init__(self, configuration_name):
        self.__configuration_name = configuration_name

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration: dict,
        dry_run: bool,
        output_file: Optional[TextIO],
    ):
        if self.__configuration_name in configuration:
            if configuration.get(f"{self.__configuration_name}|skip"):
                cli_ui.debug(
                    f"Skipping {self.__configuration_name} - explicitly configured to do so."
                )
                return
            elif (
                configuration.get("project|archive")
                and self.__configuration_name != "project"
            ):
                cli_ui.debug(
                    f"Skipping {self.__configuration_name} - it is configured to be archived."
                )
                return

            if dry_run:
                cli_ui.debug(f"Processing {self.__configuration_name} in dry-run mode.")
                self._print_diff(
                    project_or_project_and_group,
                    configuration.get(self.__configuration_name),
                )
            else:
                cli_ui.debug(f"Processing {self.__configuration_name}")
                self._process_configuration(project_or_project_and_group, configuration)

            if output_file:
                cli_ui.debug(
                    f"Writing effective configuration for {self.__configuration_name} to the output file."
                )
                self._write_to_file(
                    configuration.get(self.__configuration_name),
                    output_file,
                )

        else:
            logging.debug("Skipping %s - not in config." % self.__configuration_name)

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, configuration_to_process):
        cli_ui.debug(
            f"Diffing for {self.__configuration_name} section is not supported yet"
        )

    def _write_to_file(
        self,
        configuration_to_process,
        output_file: TextIO,
    ):
        """
        Writes indented content of a dict under a key from "try_to_write_header_to_output_file" method.
        """
        try:
            output_file.writelines(
                f"  {self.__configuration_name}:\n",
            )
            indented_configuration = textwrap.indent(
                yaml.dump(
                    configuration_to_process,
                    default_flow_style=False,
                ),
                "    ",
            )
            output_file.write(indented_configuration)
        except Exception as e:
            logging.error(f"Error when trying to write to {output_file.name}: {e}")
            raise e
