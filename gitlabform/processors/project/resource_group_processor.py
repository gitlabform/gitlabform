from cli_ui import debug as verbose
from cli_ui import fatal
from gitlabform import EXIT_INVALID_INPUT

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ResourceGroupProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("resource_group", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        config_resource_group_name = configuration["resource_group"]["name"]
        config_process_mode = configuration["resource_group"]["process_mode"]

        gitlab_resource_group = self.gitlab.get_specific_resource_group(
            project_and_group, config_resource_group_name
        )

        if gitlab_resource_group:
            # the project is configured to use the provided resource group
            if config_process_mode != gitlab_resource_group["process_mode"]:
                # check the resource group process mode diff comparing config entity and gitlab entity
                response = self.gitlab.update_resource_group(
                    project_and_group,
                    config_resource_group_name,
                    {"process_mode": config_process_mode},
                )
                # an invalid process mode will return an empty response
                if not response:
                    fatal(
                        f"process_mode does not have a valid value: {config_process_mode}\n",
                        exit_code=EXIT_INVALID_INPUT,
                    )
                else:
                    verbose(
                        f"Setting resource group process mode to {config_process_mode}"
                    )
        else:
            fatal(
                f"Project is not configured to use resource group {config_resource_group_name}\n",
                exit_code=EXIT_INVALID_INPUT,
            )
