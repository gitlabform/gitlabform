from logging import debug
from cli_ui import debug as verbose
from cli_ui import fatal

import abc
from typing import Callable, List

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.defining_keys import AbstractKey


class MultipleEntitiesProcessor(AbstractProcessor, metaclass=abc.ABCMeta):
    def __init__(
        self,
        configuration_name: str,
        gitlab: GitLab,
        list_method_name: str,
        add_method_name: str,
        delete_method_name: str,
        defining: AbstractKey,
        required_to_create_or_update: AbstractKey,
        edit_method_name=None,
    ):
        super().__init__(configuration_name, gitlab)
        self.list_method: Callable = getattr(self.gitlab, list_method_name)
        self.add_method: Callable = getattr(self.gitlab, add_method_name)
        self.delete_method: Callable = getattr(self.gitlab, delete_method_name)
        self.defining: AbstractKey = defining
        self.required_to_create_or_update: AbstractKey = required_to_create_or_update

        if edit_method_name:
            self.edit_method: Callable = getattr(self.gitlab, edit_method_name)
        else:
            self.edit_method = None

    def _can_proceed(self, project_or_group: str, configuration: dict):
        return True

    def _process_configuration(self, project_or_group: str, configuration: dict):

        if not self._can_proceed(project_or_group, configuration):
            return

        entities_in_configuration = configuration[self.configuration_name]

        # TODO: move/convert this to a configuration validation phase
        self._find_duplicates(project_or_group, entities_in_configuration)

        entities_in_gitlab = self.list_method(project_or_group)
        debug(f"{self.configuration_name} BEFORE: ^^^")

        # 1. group entities into 3 groups:
        # a) only in configuration,
        # b) in both configuration and gitlab (matching defining keys),
        # c) only in gitlab,

        # 2. if "enforce", then delete c)
        # TODO: implement this.

        # 3. update b), if needed (or delete them if marked as "delete")

        # 4. add a) (or do nothing if marked as "delete")

        for entity_name, entity_config in entities_in_configuration.items():

            entity_in_gitlab = self._is_in_gitlab(entity_config, entities_in_gitlab)
            if entity_in_gitlab:
                if entity_config.get("delete", False):
                    self._validate_required_to_delete(
                        project_or_group, entity_name, entity_config
                    )
                    verbose(
                        f"Deleting {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.delete_method(project_or_group, entity_in_gitlab)
                elif self._needs_update(entity_in_gitlab, entity_config):
                    self._validate_required_to_create_or_update(
                        project_or_group, entity_name, entity_config
                    )
                    if self.edit_method:
                        verbose(
                            f"Editing {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.edit_method(
                            project_or_group, entity_in_gitlab, entity_config
                        )
                        debug(f"{self.configuration_name} AFTER: ^^^")
                    else:
                        verbose(
                            f"Recreating {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.delete_method(project_or_group, entity_in_gitlab)
                        self.add_method(project_or_group, entity_config)
                        debug(f"{self.configuration_name} AFTER: ^^^")
                else:
                    verbose(
                        f"{entity_name} of {self.configuration_name} in {project_or_group} doesn't need an update."
                    )
            else:
                if entity_config.get("delete", False):
                    verbose(
                        f"{entity_name} of {self.configuration_name} in {project_or_group} already doesn't exist."
                    )
                else:
                    self._validate_required_to_create_or_update(
                        project_or_group, entity_name, entity_config
                    )
                    verbose(
                        f"Adding {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.add_method(project_or_group, entity_config)
                    debug(f"{self.configuration_name} AFTER: ^^^")

    def _find_duplicates(self, project_or_group: str, entities_in_configuration: dict):
        for first_key, first_value in entities_in_configuration.items():
            for second_key, second_value in entities_in_configuration.items():
                if first_key != second_key:
                    if self.defining.matches(first_value, second_value):
                        fatal(
                            f"Entities {first_key} and {second_key} in {self.configuration_name} for {project_or_group}"
                            f" are the same in terms of their defining keys: {self.defining.explain()}",
                            exit_code=EXIT_INVALID_INPUT,
                        )

    def _validate_required_to_create_or_update(
        self, project_or_group: str, entity_name: str, entity_dict: dict
    ):
        if not self.required_to_create_or_update.contains(entity_dict):
            fatal(
                f"Entity {entity_name} in {self.configuration_name} for {project_or_group}"
                f" doesn't have some of its keys required to create or update:"
                f" {self.required_to_create_or_update.explain()}",
                exit_code=EXIT_INVALID_INPUT,
            )

    def _validate_required_to_delete(
        self, project_or_group: str, entity_name: str, entity_dict: dict
    ):
        if not self.defining.contains(entity_dict):
            fatal(
                f"Entity {entity_name} in {self.configuration_name} for {project_or_group}"
                f" doesn't have some of its defining keys required to delete it: {self.defining.explain()}",
                exit_code=EXIT_INVALID_INPUT,
            )

    def _is_in_gitlab(
        self, entity_in_configuration: dict, entities_in_gitlab: List[dict]
    ):
        for entity_in_gitlab in entities_in_gitlab:
            if self.defining.matches(entity_in_gitlab, entity_in_configuration):
                return entity_in_gitlab

        return False
