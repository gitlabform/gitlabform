from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class IntegrationsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("integrations", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for integration in sorted(configuration["integrations"]):
            if configuration.get("integrations|" + integration + "|delete"):
                verbose(f"Deleting integration: {integration}")
                self.gitlab.delete_integration(project_and_group, integration)
            else:
                verbose(f"Setting integration: {integration}")
                self.gitlab.set_integration(
                    project_and_group,
                    integration,
                    configuration["integrations"][integration],
                )
