from cli_ui import debug

from gitlab.exceptions import GitlabDeleteError
from gitlab.v4.objects import Project, ProjectIntegration
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class IntegrationsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("integrations", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        configured_integrations = configuration.get("integrations", {})
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for integration in sorted(configured_integrations):
            gl_integration: ProjectIntegration = project.integrations.get(integration, lazy=True)

            if configured_integrations[integration].get("delete"):
                debug(f"Deleting integration: {integration}")
                try:
                    gl_integration.delete()
                except GitlabDeleteError as e:
                    # If we get a 404 the integration does not exist, so we can ignore the error
                    if e.response_code == 404:
                        debug(f"Integration {integration} does not exist, skipping deletion.")
                    else:
                        debug(f"Failed to delete integration {integration}: {e}")
                        raise
            else:
                debug(f"Setting integration: {integration}")
                project.integrations.update(integration, configured_integrations[integration])
