from logging import debug
from typing import List, Tuple, Union

from gitlab.exceptions import GitlabGetError, GitlabParsingError
from gitlab.v4.objects.projects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ProjectTopicsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_topics", gitlab)

    def _process_configuration(self, project_path: str, configuration: dict):
        project_topics: Dict = configuration.get("project_topics", {})
        configured_project_topics_key: List[str] = project_topics.get("topics", [])

        project: Project = self.gl.get_project_by_path_cached(project_path)

        existing_topics: List[str] = project.topics

        # needs update takes a dict but existing_push_topics is a List

        # List of topics not having delete = true or no delete attribute at all
        topics_to_add: List[str] = [
            t if isinstance(t, str) else list(t.keys())[0]
            for t in configured_project_topics_key
            if isinstance(t, str) or not list(t.values())[0].get("delete", False)
        ]

        # List of topics having delete = true
        topics_to_delete: List[str] = [
            list(t.keys())[0]
            for t in configured_project_topics_key
            if isinstance(t, dict) and list(t.values())[0].get("delete") is True
        ]

        # if no pre-existing topics or enforce is set to true, just set topics
        if not existing_topics or project_topics.get("enforce", False):
            debug(
                f"No existing topics for '{project.name} or enforce: true', setting topics."
            )
            self.set_project_topics(project, topics_to_add)
            return

        self.update_project_topics(existing_topics, topics_to_add, topics_to_delete)

    @staticmethod
    def update_project_topics(
        project: Project,
        existing_topics: List[str],
        topics_to_add: List[str],
        topics_to_delete: List[str],
    ):
        topics: List[str] = list(str)

        topics.extend(existing_topics)
        topics.extend(topics_to_add)

        topics = [topic for topic in topics if topic not in topics_to_delete]

        if not topics:
            debug("No update needed for Project Topics")
            return

        debug(f"Updating topics to {str(topics)}")

        # Save the updated topics to the project
        project.topics = topics
        project.save()

    @staticmethod
    def set_project_topics(project: Project, project_topics: list):
        debug(f"Creating topics with configuration: {project_topics}")
        project.topics = project_topics
        project.save()
