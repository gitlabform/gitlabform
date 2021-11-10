from abc import ABC, abstractmethod

from cli_ui import debug as verbose

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
                verbose(
                    f"Skipping section '{self.configuration_name}' - explicitly configured to do so."
                )
                return
            elif (
                configuration.get("project|archive")
                and self.configuration_name != "project"
            ):
                verbose(
                    f"Skipping section '{self.configuration_name}' - it is configured to be archived."
                )
                return

            if dry_run:
                verbose(
                    f"Processing section '{self.configuration_name}' in dry-run mode."
                )
                self._print_diff(
                    project_or_project_and_group,
                    configuration.get(self.configuration_name),
                )
            else:
                verbose(f"Processing section '{self.configuration_name}'")
                self._process_configuration(project_or_project_and_group, configuration)

            effective_configuration.add_configuration(
                project_or_project_and_group,
                self.configuration_name,
                configuration.get(self.configuration_name),
            )
        else:
            verbose(f"Skipping section '{self.configuration_name}' - not in config.")

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, configuration_to_process):
        verbose(f"Diffing for section '{self.configuration_name}' is not supported yet")
