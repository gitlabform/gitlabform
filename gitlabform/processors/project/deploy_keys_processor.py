import logging

import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployKeysProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_keys")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        logging.debug(
            "Deploy keys BEFORE: %s", self.gitlab.get_deploy_keys(project_and_group)
        )
        for deploy_key in sorted(configuration["deploy_keys"]):
            cli_ui.debug(f"Setting deploy key: {deploy_key}")
            self.gitlab.post_deploy_key(
                project_and_group, configuration["deploy_keys"][deploy_key]
            )
        logging.debug(
            "Deploy keys AFTER: %s", self.gitlab.get_deploy_keys(project_and_group)
        )
