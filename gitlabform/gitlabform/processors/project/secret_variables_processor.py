import logging

import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class SecretVariablesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("secret_variables")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        if (
            self.gitlab.get_project_settings(project_and_group)["builds_access_level"]
            == "disabled"
        ):
            cli_ui.warning(
                "Builds disabled in this project so I can't set secret variables here."
            )
            return

        logging.debug(
            "Secret variables BEFORE: %s",
            self.gitlab.get_secret_variables(project_and_group),
        )

        for secret_variable in sorted(configuration["secret_variables"]):

            if "delete" in configuration["secret_variables"][secret_variable]:
                key = configuration["secret_variables"][secret_variable]["key"]
                if configuration["secret_variables"][secret_variable]["delete"]:
                    cli_ui.debug(
                        f"Deleting {secret_variable}: {key} in project {project_and_group}"
                    )
                    try:
                        self.gitlab.delete_secret_variable(project_and_group, key)
                    except:
                        logging.warn(
                            f"Could not delete variable {key} in group {project_and_group}"
                        )
                    continue

            cli_ui.debug(f"Setting secret variable: {secret_variable}")
            try:
                self.gitlab.put_secret_variable(
                    project_and_group,
                    configuration["secret_variables"][secret_variable],
                )
            except NotFoundException:
                self.gitlab.post_secret_variable(
                    project_and_group,
                    configuration["secret_variables"][secret_variable],
                )

        logging.debug(
            "Secret variables AFTER: %s",
            self.gitlab.get_secret_variables(project_and_group),
        )
