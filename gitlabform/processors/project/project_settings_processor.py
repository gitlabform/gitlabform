import os
from logging import debug, error, warning, info
from typing import Callable, Dict, List

from gitlab import GitlabGetError, GitlabUpdateError
from gitlab.v4.objects import Project
from gql.transport.exceptions import TransportQueryError

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


class ProjectSettingsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("project_settings", gitlab)
        self.get_entity_in_gitlab: Callable = getattr(self, "get_project_settings")

    def _process_configuration(self, project_path: str, configuration: dict) -> None:
        debug("Processing project settings...")
        project: Project = self.gl.get_project_by_path_cached(project_path)

        project_settings_in_config = configuration.get("project_settings", {})
        project_settings_in_gitlab = project.asdict()
        debug(project_settings_in_gitlab)
        debug("project_settings BEFORE: ^^^")

        self._process_project_topics(project_settings_in_config, project_settings_in_gitlab)

        # Remove avatar from config to process it last
        avatar_config = project_settings_in_config.pop("avatar", None)

        # Remove duo_features_enabled from config as it can't be processed via the REST Api and if it's the only
        # config defined for a Project, Gitlab will reject with error the REST update() request
        duo_features_enabled_in_config = project_settings_in_config.pop("duo_features_enabled", None)

        # Process other settings first
        if self._needs_update(project_settings_in_gitlab, project_settings_in_config):
            debug("Updating project settings")
            for key, value in project_settings_in_config.items():
                debug(f"Updating setting {key} to value {value}")
                setattr(project, key, value)
            project.save()

            debug(project.asdict())
            debug("project_settings AFTER: ^^^")
        else:
            debug("No update needed for project settings")

        # Process duo_features_enabled
        self._process_duo_features_enabled(project, duo_features_enabled_in_config)

        # Process avatar last - with error handling that doesn't stop execution
        if avatar_config is not None:
            try:
                self._process_project_avatar(project, {"avatar": avatar_config})
            except Exception as e:
                warning(f"Failed to process project avatar: {e}")
                raise e

    def get_project_settings(self, project_path: str):
        """Get project settings from GitLab."""
        return self.gl.get_project_by_path_cached(project_path).asdict()

    def _print_diff(self, project_or_project_and_group: str, entity_config, diff_only_changed: bool):
        entity_in_gitlab = self.get_project_settings(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )

    def _process_project_topics(self, project_settings_in_config: Dict, project_settings_in_gitlab: Dict) -> None:
        project_settings_topics: Dict = project_settings_in_config.get("topics", [])

        if not project_settings_topics:
            return

        keep_existing: bool = False

        for i, topic in enumerate(project_settings_topics):
            if isinstance(topic, dict) and "keep_existing" in topic:
                value = topic["keep_existing"]
                if isinstance(value, bool):
                    keep_existing = value
                    del project_settings_topics[i]
                    break

        adjusted_project_topics_to_set: List[str] = []

        if keep_existing:
            adjusted_project_topics_to_set.extend(project_settings_in_gitlab.get("topics", []))

        # List of topics not having delete = true or no delete attribute at all
        topics_to_add: List[str] = [
            list(t.keys())[0] if isinstance(t, dict) else t
            for t in project_settings_topics
            if isinstance(t, str) or (isinstance(t, dict) and not list(t.values())[0].get("delete", False))
        ]

        # List of topics having delete = true
        topics_to_delete: List[str] = [
            list(t.keys())[0]
            for t in project_settings_topics
            if isinstance(t, dict) and list(t.values())[0].get("delete") is True
        ]

        adjusted_project_topics_to_set.extend(topics_to_add)

        adjusted_project_topics_to_set = [
            topic for topic in adjusted_project_topics_to_set if topic not in topics_to_delete
        ]

        debug(f"topics after adjustment: {adjusted_project_topics_to_set}")

        project_settings_in_config["topics"] = adjusted_project_topics_to_set

    def _process_project_avatar(self, project: Project, project_settings_in_config: dict) -> None:
        """Process project avatar settings from configuration."""
        debug("Processing project avatar configuration")

        avatar_path = project_settings_in_config.get("avatar")
        if avatar_path is None:
            debug("No avatar configuration provided, skipping avatar processing")
            return

        debug(f"Avatar configuration found: {avatar_path}")

        # Check current avatar status
        current_avatar = getattr(project, "avatar_url", None)

        if avatar_path == "":
            # Want to remove avatar
            if not current_avatar:
                debug("Avatar already empty, no update needed")
                return
            debug("Deleting project avatar")
            project.avatar = ""
            project.save()
            debug("Project avatar deleted successfully")
            return

        # Resolve relative paths to absolute paths
        if not os.path.isabs(avatar_path):
            # Convert relative path to absolute path relative to current working directory
            avatar_path = os.path.abspath(avatar_path)
            debug(f"Resolved relative path to absolute path: {avatar_path}")

        # Want to set avatar from file
        debug(f"Setting project avatar from file: {avatar_path}")
        try:
            with open(avatar_path, "rb") as avatar_file:
                project.avatar = avatar_file
                project.save()
            debug("Project avatar uploaded successfully")
        except FileNotFoundError:
            error_msg = f"Project avatar file not found: {avatar_path}"
            error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Error uploading project avatar: {str(e)}"
            error(error_msg)
            raise Exception(error_msg) from e

    def _process_duo_features_enabled(self, project: Project, duo_features_enabled_in_config: None | bool):
        if duo_features_enabled_in_config is None:
            info(
                f"duo_features_enabled is not defined in Config for project {project.path_with_namespace}, will not make any changes."
            )
            return

        duo_features_enabled_in_gl = self._get_project_duo_features_enabled_from_gitlab(project)
        if duo_features_enabled_in_gl == duo_features_enabled_in_config:
            debug("No changes detected for duo_features_enabled")
            return

        self._set_project_duo_features_enabled(project, duo_features_enabled_in_config)

    def _get_project_duo_features_enabled_from_gitlab(self, project: Project) -> List[Dict[str, str]]:
        """Query GraphQL using Python Gitlab
        https://python-gitlab.readthedocs.io/en/stable/api-usage-graphql.html

        GETting and updating of duo_features_enabled is currently only supported through the GraphQL API:
        https://gitlab.com/gitlab-org/gitlab/-/merge_requests/143972
        """

        query = (
            """
            query ProjectDuoFeatures {
               project(fullPath: \""""
            + project.path_with_namespace
            + """\") 
              {
                   duoFeaturesEnabled
              }
           }
        """
        )
        result = self.gl.graphql.execute(query)

        if result["project"] is not None and result["project"]["duoFeaturesEnabled"] is not None:
            return result["project"]["duoFeaturesEnabled"]
        else:
            raise GitlabGetError(f"Failed to get duo_features_enabled for Project: {project.path_with_namespace}")

    def _set_project_duo_features_enabled(self, project: Project, duo_features_enabled: bool) -> None:
        """Mutate Project Settings using GraphQL with Python Gitlab"""
        duo_features_enabled_str = str(duo_features_enabled).lower()
        mutation = (
            """
           mutation Projects {
             projectSettingsUpdate(input: { fullPath: \""""
            + project.path_with_namespace
            + """\", duoFeaturesEnabled: """
            + duo_features_enabled_str
            + """ }) 
             {
                errors
             }
           }
        """
        )
        try:
            result = self.gl.graphql.execute(mutation)

            if result["errors"] is not None:
                raise GitlabUpdateError(
                    f"Failed to update duo_features_enabled for Project: {project.path_with_namespace}, to: {duo_features_enabled}: {result['errors']}"
                )
        except TransportQueryError as e:
            if e.errors is not None:
                error_message = e.errors[0].message
            else:
                error_message = "Unknown GraphQL error"
            raise GitlabUpdateError(
                f"Failed to update duo_features_enabled for Project: {project.path_with_namespace}, to: {duo_features_enabled}: {error_message}"
            )
