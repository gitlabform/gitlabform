from abc import ABC, abstractmethod
from logging import debug
from typing import Callable, Union

import requests
from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlab import Gitlab
from gitlabform.gitlab import GitlabWrapper
from gitlabform.output import EffectiveConfigurationFile
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
        self.gl: Gitlab = GitlabWrapper(self.gitlab)._gitlab

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration,
        dry_run: bool,
        effective_configuration: EffectiveConfigurationFile,
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
                self._print_diff(project_or_project_and_group, configuration)
            else:
                verbose(f"Processing section '{self.configuration_name}'")
                if self._can_proceed(project_or_project_and_group, configuration):
                    self._process_configuration_with_retries(
                        project_or_project_and_group, configuration
                    )

            effective_configuration.add_configuration(
                project_or_project_and_group,
                self.configuration_name,
                configuration.get(self.configuration_name),
            )
        else:
            verbose(f"Skipping section '{self.configuration_name}' - not in config.")

    def _section_is_in_config(self, configuration: dict):
        return self.configuration_name in configuration

    def _process_configuration_with_retries(
        self, project_or_project_and_group: str, configuration: dict
    ):
        retry = 1
        max_retries = 3

        while True:
            try:
                if retry > 1:
                    verbose(
                        f"Retrying section '{self.configuration_name}' - {retry}/{max_retries}..."
                    )

                self._process_configuration(
                    project_or_project_and_group,
                    configuration,
                )

                return
            except Exception as e:
                if retry > max_retries:
                    raise MaxProcessorRetriesExceeded from e

                if self._should_retry_processor(e):
                    retry += 1
                    continue
                else:
                    raise e

    @staticmethod
    def _should_retry_processor(e: Exception) -> bool:
        # Most possible failures during processing are handled by the HTTP request retries in GitLabCore class,
        # but in some cases we cannot do that on that level.

        # If we already retried on a request level, don't retry again
        if "Max retries exceeded with url" in str(e):
            return False

        # One case is when a POST request is made and the request is sent, but we got no (or incomplete?) response.
        # Because we don't know if the particular POST request was done under the hood (f.e. an entity was created),
        # we cannot retry just the single request (f.e. if it was created then a retry would either create a duplicate
        # of the entity or fail with an error, if duplicates are not allowed in a given case).

        # Then we need to retry the whole section (f.e. files) for a given entity (f.e. project foo/bar), so the checks
        # for the initial state will re-run (f.e. checking if that entity already exists or not).

        # fmt: off
        if type(e) == requests.exceptions.ConnectionError \
                and "RemoteDisconnected('Remote end closed connection without response')" in str(e):
            return True
        # fmt: on

        return False

    @abstractmethod
    def _process_configuration(
        self, project_or_project_and_group: str, configuration: dict
    ):
        pass

    def _print_diff(self, project_or_project_and_group: str, configuration):
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

    def _can_proceed(self, project_or_group: str, configuration: dict):
        return True


class MaxProcessorRetriesExceeded(Exception):
    pass
