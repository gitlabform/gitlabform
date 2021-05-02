import logging
import textwrap
from typing import Optional, TextIO
from abc import ABC, abstractmethod
import yaml

from gitlabform.gitlabform.processors.util.decorators import configuration_to_safe_dict


class AbstractProcessor(ABC):
    def __init__(self, configuration_name):
        self.configuration_name = configuration_name

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration: dict,
        dry_run: bool,
        output_file: Optional[TextIO],
    ):
        if self.configuration_name in configuration:
            if configuration.get(f"{self.configuration_name}|skip"):
                logging.info(
                    "Skipping %s - explicitly configured to do so."
                    % self.configuration_name
                )
                return
            elif (
                configuration.get("project|archive")
                and self.configuration_name != "project"
            ):
                logging.info(
                    "Skipping %s - it is configured to be archived."
                    % self.configuration_name
                )
                return

            if dry_run:
                logging.info("Processing %s in dry-run mode." % self.configuration_name)
                self._print_diff(
                    project_or_project_and_group,
                    configuration.get(self.configuration_name),
                )
            else:
                logging.info("Processing %s" % self.configuration_name)
                self._process_configuration(project_or_project_and_group, configuration)

            if output_file:
                logging.debug(
                    f"Writing effective configuration for {self.configuration_name} to the output file."
                )
                self._write_to_file(
                    configuration.get(self.configuration_name),
                    output_file,
                )

        else:
            logging.debug("Skipping %s - not in config." % self.configuration_name)

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, configuration_to_process):
        logging.info(
            f"Diffing for {self.configuration_name} section is not supported yet"
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
                f"  {self.configuration_name}:\n",
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
