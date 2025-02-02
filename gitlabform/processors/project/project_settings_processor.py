from logging import debug
from typing import Callable, Dict, List

from gitlab.v4.objects import Project

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

        self._process_project_topics(
            project_settings_in_config, project_settings_in_gitlab
        )

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

    def get_project_settings(self, project_path: str):
        return self.gl.get_project_by_path_cached(project_path).asdict()

    def _print_diff(
        self, project_or_project_and_group: str, entity_config, diff_only_changed: bool
    ):
        entity_in_gitlab = self.get_project_settings(project_or_project_and_group)

        DifferenceLogger.log_diff(
            f"{self.configuration_name} changes",
            entity_in_gitlab,
            entity_config,
            only_changed=diff_only_changed,
        )

    def _process_project_topics(
        self, project_settings_in_config: Dict, project_settings_in_gitlab: Dict
    ) -> None:
        project_settings_topics: Dict = project_settings_in_config.get("topics", [])

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
            adjusted_project_topics_to_set.extend(
                project_settings_in_gitlab.get("topics", [])
            )

        # List of topics not having delete = true or no delete attribute at all
        topics_to_add: List[str] = [
            list(t.keys())[0] if isinstance(t, dict) else t
            for t in project_settings_topics
            if isinstance(t, str)
            or (isinstance(t, dict) and not list(t.values())[0].get("delete", False))
        ]

        # List of topics having delete = true
        topics_to_delete: List[str] = [
            list(t.keys())[0]
            for t in project_settings_topics
            if isinstance(t, dict) and list(t.values())[0].get("delete") is True
        ]

        adjusted_project_topics_to_set.extend(topics_to_add)

        adjusted_project_topics_to_set = [
            topic
            for topic in adjusted_project_topics_to_set
            if topic not in topics_to_delete
        ]

        debug(f"topics after adjustment: {adjusted_project_topics_to_set}")

        project_settings_in_config["topics"] = adjusted_project_topics_to_set
