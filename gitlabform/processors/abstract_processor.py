from abc import ABC, abstractmethod
from logging import debug
from typing import Any, Callable, Union

from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfiguration
from gitlabform.processors.util.decorators import configuration_to_safe_dict


class AbstractProcessor(ABC):
    def __init__(self, configuration_name: str, gitlab: GitLab):
        self.configuration_name = configuration_name
        self.gitlab = gitlab
        self.custom_diff_analyzers: dict[
            str,
            Callable[
                [str, list[dict[str, Union[str, int]]], list[dict[str, int]]], bool
            ],
        ] = {}

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration,
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

    def _needs_update(
        self,
        entity_in_gitlab: dict,
        entity_in_configuration: dict,
    ):
        # in the configuration we often don't define every key value because we rely on the defaults.
        # that's why GitLab API often returns many more keys than we have in the configuration.

        # so to decide if the entity should be updated:
        # a) we look for ANY settings that are ONLY in configuration,
        # a) we compare the settings that are in both configuration and gitlab,

        keys_only_in_configuration = set(entity_in_configuration.keys()) - set(
            entity_in_gitlab.keys()
        )
        if len(keys_only_in_configuration) > 0:
            return True

        keys_on_both_sides = set(entity_in_configuration.keys()) & set(
            entity_in_gitlab.keys()
        )
        for key in keys_on_both_sides:
            if key in self.custom_diff_analyzers:
                return self.custom_diff_analyzers[key](
                    key, entity_in_gitlab[key], entity_in_configuration[key]
                )

            if entity_in_gitlab[key] != entity_in_configuration[key]:
                debug(
                    f"entity_in_gitlab[{key}] -> {entity_in_gitlab[key]} != entity_in_configuration[{key}] -> {entity_in_configuration[key]}"
                )
                return True

        return False

    @staticmethod
    def recursive_diff_analyzer(cfg_key: str, cfg_in_gitlab: list, local_cfg: list):
        """
        :return: True if the lists are NOT equal, False otherwise
        """
        if len(cfg_in_gitlab) != len(local_cfg):
            return True

        for index in range(len(cfg_in_gitlab)):
            from_gitlab = {
                k: v for k, v in cfg_in_gitlab[index].items() if v is not None
            }
            from_local_cfg = local_cfg[index]

            keys_on_both_sides = set(from_gitlab.keys()) & set(from_local_cfg.keys())

            for key in keys_on_both_sides:
                if isinstance(from_gitlab[key], list) and isinstance(
                    from_local_cfg[key], list
                ):
                    AbstractProcessor.recursive_diff_analyzer(
                        key, from_gitlab[key], from_local_cfg[key]
                    )

                if from_gitlab[key] != from_local_cfg[key]:
                    debug(
                        f"* A <{key}> in [{cfg_key}] differs:\n GitLab :: {from_gitlab} != Local :: {from_local_cfg}"
                    )
                    return True

        return False
