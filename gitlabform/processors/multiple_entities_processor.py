import logging

import cli_ui
from typing import Callable, Any

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class MultipleEntitiesProcessor(AbstractProcessor):
    def __init__(
        self,
        configuration_name: str,
        gitlab: GitLab,
        list_method_name: str,
        add_method_name: str,
        delete_method_name: str,
        defining_keys_or: list[Any],
        defining_keys_and: list[Any],
        edit_method_name: str = None,
    ):
        super().__init__(configuration_name, gitlab)
        self.list_method: Callable = getattr(self.gitlab, list_method_name)
        self.add_method: Callable = getattr(self.gitlab, add_method_name)
        self.delete_method: Callable = getattr(self.gitlab, delete_method_name)
        self.defining_keys_or: list[Any] = defining_keys_or
        self.defining_keys_and: list[Any] = defining_keys_and

        if edit_method_name:
            self.edit_method: Callable = getattr(self.gitlab, edit_method_name)
        else:
            self.edit_method = None

    def _process_configuration(self, project_or_group: str, configuration: dict):
        entities_in_gitlab = self.list_method(project_or_group)
        entities_in_configuration = configuration[self.configuration_name]

        logging.debug(f"{self.configuration_name} BEFORE: {entities_in_gitlab}")

        for entity_name, entity_config in entities_in_configuration.items():

            equivalent_entity_in_gitlab = self._is_in_gitlab(
                entity_config, entities_in_gitlab
            )
            if equivalent_entity_in_gitlab:
                if "delete" in entity_config and entity_config["delete"]:
                    cli_ui.debug(
                        f"Deleting {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.delete_method(project_or_group, entity_config)
                elif self._needs_update(equivalent_entity_in_gitlab, entity_config):
                    if self.edit_method:
                        cli_ui.debug(
                            f"Editing {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.edit_method(project_or_group, entity_config)
                    else:
                        cli_ui.debug(
                            f"Recreating {entity_name} of {self.configuration_name} in {project_or_group}"
                        )
                        self.delete_method(project_or_group, entity_config)
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
                    cli_ui.debug(
                        f"Adding {entity_name} of {self.configuration_name} in {project_or_group}"
                    )
                    self.add_method(project_or_group, entity_config)

        logging.debug(
            f"{self.configuration_name} AFTER: %s", self.list_method(project_or_group)
        )

    def _is_in_gitlab(
        self, entity_in_configuration: dict, entities_in_gitlab: list[dict]
    ):

        # we need to find an entity in GitLab that has *both*:
        #   * ALL of the defining_keys_all matching
        #   * at least one of the defining_keys_or matching

        for entity_in_gitlab in entities_in_gitlab:

            keys_or_match = False
            for key in self.defining_keys_or:
                if (
                    key in entity_in_configuration
                    and key in entity_in_gitlab
                    and entity_in_configuration[key] == entity_in_gitlab[key]
                ):
                    keys_or_match = True
                    break

            if not keys_or_match:
                continue

            keys_and_match = True
            for key in self.defining_keys_and:
                if (
                    key not in entity_in_configuration
                    or key not in entity_in_gitlab
                    or entity_in_configuration[key] != entity_in_gitlab[key]
                ):
                    keys_and_match = False
                    break

            if keys_or_match and keys_and_match:
                return entity_in_gitlab

        return False

    def _needs_update(
        self,
        entity_in_gitlab: dict,
        entity_in_configuration: dict,
    ):

        # when we get some entity from GitLab API we may get a lot of parameters that hold
        # values equal to the default. if they are not defined at all in the configuration
        # then we should ignore them.
        for key in entity_in_gitlab.keys():
            if key in entity_in_configuration.keys():
                if entity_in_gitlab[key] != entity_in_configuration[key]:
                    return True

        return False
