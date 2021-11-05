from logging import debug
from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployKeysProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_keys", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        debug("Deploy keys BEFORE: %s", self.gitlab.get_deploy_keys(project_and_group))
        for deploy_key in sorted(configuration["deploy_keys"]):
            verbose(f"Setting deploy key: {deploy_key}")
            self.gitlab.post_deploy_key(
                project_and_group, configuration["deploy_keys"][deploy_key]
            )
        debug("Deploy keys AFTER: %s", self.gitlab.get_deploy_keys(project_and_group))
