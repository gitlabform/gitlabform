from logging import info

from gitlab.exceptions import GitlabDeleteError
from gitlab.v4.objects import Project, ProjectIntegration
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class IntegrationsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("integrations", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        # Remove 'enforce' key from the config so that it's not treated as an integration
        configured_integrations = {
            name: settings for name, settings in configuration.get("integrations", {}).items() if name != "enforce"
        }
        enforce_integrations = configuration.get("integrations|enforce", False)
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for integration in sorted(configured_integrations):
            gl_integration: ProjectIntegration = project.integrations.get(integration, lazy=True)

            if configured_integrations[integration].get("delete"):
                info(f"Deleting integration: {integration}")
                try:
                    gl_integration.delete()
                except GitlabDeleteError as e:
                    # If we get a 404 the integration does not exist, so we can ignore the error
                    if e.response_code == 404:
                        info(f"Integration {integration} does not exist, skipping deletion.")
                    else:
                        info(f"Failed to delete integration {integration}: {e}")
                        raise
            else:
                info(f"Setting integration: {integration}")
                project.integrations.update(integration, configured_integrations[integration])

        if enforce_integrations:
            info("Deleting integrations not in configuration because enforce is enabled")
            for existing_integration in project.integrations.list(get_all=True):
                if existing_integration.slug not in configured_integrations:
                    info(f"Deleting integration: {existing_integration.slug}, because it is not in configuration")
                    existing_integration.delete()
