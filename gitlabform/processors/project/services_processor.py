from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ServicesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("services", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for service in sorted(configuration["services"]):
            if configuration.get("services|" + service + "|delete"):
                verbose(f"Deleting service: {service}")
                self.gitlab.delete_service(project_and_group, service)
            else:

                verbose(f"Setting service: {service}")
                self.gitlab.set_service(
                    project_and_group, service, configuration["services"][service]
                )
