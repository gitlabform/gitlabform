import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ServicesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("services")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for service in sorted(configuration["services"]):
            if configuration.get("services|" + service + "|delete"):
                cli_ui.debug(f"Deleting service: {service}")
                self.gitlab.delete_service(project_and_group, service)
            else:

                if (
                    "recreate" in configuration["services"][service]
                    and configuration["services"][service]["recreate"]
                ):
                    # support from this configuration key has been added in v1.13.4
                    # we will remove it here to avoid passing it to the GitLab API
                    cli_ui.warning(
                        f"Ignoring deprecated 'recreate' field in the '{service}' service config. "
                        "Please remove it from the config file permanently as this workaround is not "
                        "needed anymore."
                    )
                    del configuration["services"][service]["recreate"]

                cli_ui.debug(f"Setting service: {service}")
                self.gitlab.set_service(
                    project_and_group, service, configuration["services"][service]
                )
