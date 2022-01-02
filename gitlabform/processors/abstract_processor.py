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
        if self._section_is_in_config(configuration):
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

    def _section_is_in_config(self, configuration: dict):
        return self.configuration_name in configuration

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, entity_config):
        verbose(f"Diffing for section '{self.configuration_name}' is not supported yet")

    @staticmethod
    def _needs_update(
        entity_in_gitlab: dict,
        entity_in_configuration: dict,
    ):
        # in configuration we often don't define every key value because we rely on the defaults.
        # that's why GitLab API often returns many more keys than we have in the configuration.
        # so to decide if the entity should be update we are checking only the values of the ones
        # that are in the configuration.

        for key in entity_in_gitlab.keys():
            if key in entity_in_configuration.keys():
                if entity_in_gitlab[key] != entity_in_configuration[key]:
                    return True

        return False
