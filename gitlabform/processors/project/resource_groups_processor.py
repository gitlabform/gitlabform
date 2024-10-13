from cli_ui import debug as verbose
from cli_ui import warning

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

from gitlab import GitlabGetError
from gitlab.v4.objects import Project, ProjectResourceGroup

class ResourceGroupsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("resource_groups", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        configured_resource_groups: dict = configuration.get("resource_groups", {})
        ensure_exists: bool = configuration.get("resource_groups|ensure_exists", True)

        # Remove 'ensure_exists' from config so that it's not treated as a 'resource group'
        if "ensure_exists" in configured_resource_groups:
            configured_resource_groups.pop("ensure_exists")

        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for config_resource_group_name in sorted(configured_resource_groups):
            config_resource_group_process_mode = configured_resource_groups[config_resource_group_name]["process_mode"]
            try:
                resource_group_in_gitlab: ProjectResourceGroup = project.resource_groups.get(config_resource_group_name)
            except GitlabGetError:
                message = (
                    f"Project is not configured to use resource group: {config_resource_group_name}.\n"
                    f"Add the resource group in your project's .gitlab-ci.yml file.\n"
                    f"For more information, visit https://docs.gitlab.com/ee/ci/resource_groups/#add-a-resource-group.\n"
                    f"Or add 'ensure_exists: false' to gitlabform config to continue processing.\n"
                    f"For more information, visit https://gitlabform.github.io/gitlabform/reference/resource_groups\n"
                )
                if ensure_exists:
                    raise Exception(message)
                else:
                    warning(message)
                    continue

            if resource_group_in_gitlab and resource_group_in_gitlab.process_mode != config_resource_group_process_mode:
                verbose("Updating process mode of '%s' resource group to '%s'", config_resource_group_name, config_resource_group_process_mode)
                resource_group_in_gitlab.process_mode = config_resource_group_process_mode
                resource_group_in_gitlab.save()
