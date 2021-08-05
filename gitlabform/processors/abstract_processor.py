from abc import ABC, abstractmethod

import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfiguration
from gitlabform.processors.util.decorators import configuration_to_safe_dict


class AbstractProcessor(ABC):
    def __init__(self, configuration_name: str, gitlab: GitLab):
        self.configuration_name = configuration_name
        self.gitlab = gitlab

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration: dict,
        dry_run: bool,
        effective_configuration: EffectiveConfiguration,
    ):
        if self.configuration_name in configuration:
            if configuration.get(f"{self.configuration_name}|skip"):
                cli_ui.debug(
                    f"Skipping {self.configuration_name} - explicitly configured to do so."
                )
                return
            elif (
                configuration.get("project|archive")
                and self.configuration_name != "project"
            ):
                cli_ui.debug(
                    f"Skipping {self.configuration_name} - it is configured to be archived."
                )
                return

            if dry_run:
                cli_ui.debug(f"Processing {self.configuration_name} in dry-run mode.")
                self._print_diff(
                    project_or_project_and_group,
                    configuration.get(self.configuration_name),
                )
            else:
                cli_ui.debug(f"Processing {self.configuration_name}")
                self._process_configuration(project_or_project_and_group, configuration)

            cli_ui.debug(
                f"Adding effective configuration for {self.configuration_name}."
            )
            effective_configuration.add_configuration(
                project_or_project_and_group,
                self.configuration_name,
                configuration.get(self.configuration_name),
            )
        else:
            cli_ui.debug(f"Skipping {self.configuration_name} - not in config.")

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, configuration_to_process):
        cli_ui.debug(
            f"Diffing for {self.configuration_name} section is not supported yet"
        )
