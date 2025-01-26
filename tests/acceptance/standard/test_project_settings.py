from typing import List
from tests.acceptance import run_gitlabform
from gitlab import Gitlab
from gitlab.v4.objects import Project


class TestProjectSettings:
    def test__builds_for_private_projects(self, gl, project):
        assert project.visibility == "private"

        config_builds_for_private_projects = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              visibility: internal
        """

        run_gitlabform(config_builds_for_private_projects, project)

        project = gl.projects.get(project.id)
        assert project.visibility == "internal"

    def test__edit_project_settings_topics_default(
        self, gl: Gitlab, project: Project
    ) -> None:
        project.topics = ["topicA", "topicB"]
        project.save()

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - topicC
                - topicD
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicC" in project_topics
        assert "topicD" in project_topics

    def test__edit_project_settings_topics_keep_existing(
        self, gl: Gitlab, project: Project
    ) -> None:
        project.topics = ["topicA", "topicB"]
        project.save()

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - keep_existing: true
                - topicC
                - topicD
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 4
        assert "topicA" in project_topics
        assert "topicB" in project_topics
        assert "topicC" in project_topics
        assert "topicD" in project_topics

    def test__delete_project_topics(self, gl: Gitlab, project: Project) -> None:
        project.topics = ["topicA", "topicB"]
        project.save()

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - keep_existing: true
                - topicA:
                    delete: true
                - topicC
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicB" in project_topics
        assert "topicC" in project_topics
