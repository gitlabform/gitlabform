import pytest
from gitlab import Gitlab, GraphQL
from gitlab.v4.objects import Project, Group

from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestProjectSettings:
    def test__can_set_duo_features_enabled(
        self, gl: Gitlab, gl_graphql: GraphQL, group: Group, project: Project, other_project: Project
    ) -> None:
        instance_settings = gl.settings.get()
        instance_settings.duo_features_enabled = True
        instance_settings.lock_duo_features_enabled = False
        instance_settings.save()

        # Set up the parent Group to have Duo features enabled but by default set to off for sub-groups and projects
        group.duo_features_enabled = True
        group.duo_availability = "default_off"
        group.save()

        config_builds_for_private_projects: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
                duo_features_enabled: true
          {other_project.path_with_namespace}:
            project_settings:
                duo_features_enabled: false
        """

        run_gitlabform(config_builds_for_private_projects, project)
        assert self.project_duo_features_enabled(gl_graphql, project.path_with_namespace) is True

        run_gitlabform(config_builds_for_private_projects, other_project)
        assert self.project_duo_features_enabled(gl_graphql, other_project.path_with_namespace) is False

        instance_settings = gl.settings.get()
        instance_settings.duo_features_enabled = False
        instance_settings.save()

    @staticmethod
    def project_duo_features_enabled(gl_graphql: GraphQL, project_path: str) -> bool:
        """
        Queries GraphQL to get the Project's duo features enabled state, as this is not available via the REST API.
        """

        query = (
            """
            {
              project(fullPath: \""""
            + project_path
            + """\") 
              {
                   duoFeaturesEnabled
              }
            }
            """
        )
        graphql_response = gl_graphql.execute(query)
        assert graphql_response["project"] is not None
        return graphql_response["project"]["duoFeaturesEnabled"]
