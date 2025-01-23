from logging import debug
from typing import List
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab.v4.objects.projects import Project
from gitlab.exceptions import GitlabGetError, GitlabParsingError


class ProjectTopicsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project_topics", gitlab)

    def _process_configuration(self, project_path: str, configuration: dict):
        configured_project_topics: List[str] = configuration.get("project_topics", {})
        project: Project = self.gl.get_project_by_path_cached(project_path)

        existing_topics: List[str] = project.topics

        if not existing_topics:
            debug(f"No existing topics for '{project.name}', creating new topics.")
            self.create_project_topics(project, configured_project_topics)
            return

        # needs update takes a dict but existing_push_topics is a List

        if self._needs_update(existing_topics, configured_project_topics):
            self.update_project_topics(existing_topics, configured_project_topics)
        else:
            debug("No update needed for Project Topics")

    @staticmethod
    def update_project_topics(
        project: Project,
        push_topics: List[str],
        configured_project_push_topics: List[str],
    ):
        topics: List[str] = list(str)

        topics.extend(push_topics)
        topics.extend(configured_project_push_topics)

        debug(f"Updating topics to {str(topics)}")
        project.topics = topics

        project.save()

    @staticmethod
    def create_project_topics(project: Project, project_topics: list):
        debug(f"Creating topics with configuration: {project_topics}")
        project.topics = project_topics
        project.save()
