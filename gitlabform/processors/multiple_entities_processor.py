import logging

import abc
import cli_ui
from typing import Callable

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.defining_keys import Key


class MultipleEntitiesProcessor(AbstractProcessor, metaclass=abc.ABCMeta):
    def __init__(
        self,
        configuration_name: str,
        gitlab: GitLab,
        list_method_name: str,
        add_method_name: str,
        delete_method_name: str,
        defining: Key,
        required_to_create_or_update: Key,
        edit_method_name=None,
    ):
        super().__init__(configuration_name, gitlab)
        self.list_method: Callable = getattr(self.gitlab, list_method_name)
        self.add_method: Callable = getattr(self.gitlab, add_method_name)
        self.delete_method: Callable = getattr(self.gitlab, delete_method_name)
        self.defining: Key = defining
        self.required_to_create_or_update: Key = required_to_create_or_update

        if edit_method_name:
            self.edit_method: Callable = getattr(self.gitlab, edit_method_name)
        else:
            self.edit_method = None

    def _process_configuration(self, project_or_group: str, configuration: dict):

        entities_in_configuration = configuration[self.configuration_name]

        self._find_duplicates(project_or_group, entities_in_configuration)

        entities_in_gitlab = self.list_method(project_or_group)
        logging.debug(f"{self.configuration_name} BEFORE: {entities_in_gitlab}")

        for entity_name, entity_config in entities_in_configuration.items():

            entity_in_gitlab = self._is_in_gitlab(entity_config, entities_in_gitlab)
            if entity_in_gitlab:
                if "delete" in entity_config and entity_config["delete"]:
                    self._validate_required_to_delete(
                        project_or_group, entity_name, entity_config
                    )
                    cli_ui.debug(
                        f"Deleting {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.delete_method(project_or_group, entity_in_gitlab)
                elif self._needs_update(entity_in_gitlab, entity_config):
                    self._validate_required_to_create_or_update(
                        project_or_group, entity_name, entity_config
                    )
                    if self.edit_method:
                        cli_ui.debug(
                            f"Editing {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.edit_method(
                            project_or_group, entity_in_gitlab, entity_config
                        )
                    else:
                        cli_ui.debug(
                            f"Recreating {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.delete_method(project_or_group, entity_in_gitlab)
                        self.add_method(project_or_group, entity_config)
                else:
                    cli_ui.debug(
                        f"{entity_name} of {self.configuration_name} in {project_or_group} doesn't need an update."
                    )
            else:
                if "delete" in entity_config and entity_config["delete"]:
                    cli_ui.debug(
                        f"{entity_name} of {self.configuration_name} in {project_or_group} already doesn't exist."
                    )
                else:
                    self._validate_required_to_create_or_update(
                        project_or_group, entity_name, entity_config
                    )
                    cli_ui.debug(
                        f"Adding {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.add_method(project_or_group, entity_config)

        logging.debug(
            f"{self.configuration_name} AFTER: %s", self.list_method(project_or_group)
        )

    def _find_duplicates(self, project_or_group: str, entities_in_configuration: dict):
        for first_key, first_value in entities_in_configuration.items():
            for second_key, second_value in entities_in_configuration.items():
                if first_key != second_key:
                    if self.defining.matches(first_value, second_value):
                        cli_ui.fatal(
                            f"Entities {first_key} and {second_key} in {self.configuration_name} for {project_or_group}"
                            f" are the same in terms of their defining keys: {self.defining.explain()}",
                            exit_code=EXIT_INVALID_INPUT,
                        )

    def _validate_required_to_create_or_update(
        self, project_or_group: str, entity_name: str, entity_dict: dict
    ):
        if not self.required_to_create_or_update.contains(entity_dict):
            cli_ui.fatal(
                f"Entity {entity_name} in {self.configuration_name} for {project_or_group}"
                f" doesn't have some of its keys required to create or update: {self.required_to_create_or_update.explain()}",
                exit_code=EXIT_INVALID_INPUT,
            )

    def _validate_required_to_delete(
        self, project_or_group: str, entity_name: str, entity_dict: dict
    ):
        if not self.defining.contains(entity_dict):
            cli_ui.fatal(
                f"Entity {entity_name} in {self.configuration_name} for {project_or_group}"
                f" doesn't have some of its defining keys required to delete it: {self.defining.explain()}",
                exit_code=EXIT_INVALID_INPUT,
            )

    def _is_in_gitlab(
        self, entity_in_configuration: dict, entities_in_gitlab: list[dict]
    ):
        for entity_in_gitlab in entities_in_gitlab:
            if self.defining.matches(entity_in_gitlab, entity_in_configuration):
                return entity_in_gitlab

        return False

    def _needs_update(
        self,
        entity_in_gitlab: dict,
        entity_in_configuration: dict,
    ):
        # in configuration we often don't define every key value because we rely on the defaults.
        # that's why GitLab API often returns many more keys than

        # when we get some entity from GitLab API we may get a lot of parameters that hold
        # values equal to the default. if they are not defined at all in the configuration
        # then we should ignore them.
        for key in entity_in_gitlab.keys():
            if key in entity_in_configuration.keys():
                if entity_in_gitlab[key] != entity_in_configuration[key]:
                    return True

        return False
