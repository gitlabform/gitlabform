from typing import List

from gitlab import Gitlab
from gitlab.v4.objects import Project
from tests.acceptance import run_gitlabform


class TestProjectSettings:
    def test__builds_for_private_projects(self, gl: Gitlab, project: Project) -> None:
        """
        Test that we can change visibility from private to internal
        """
        assert project.visibility == "private"

        config_builds_for_private_projects: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              visibility: internal
        """

        run_gitlabform(config_builds_for_private_projects, project)

        updated_project: Project = gl.projects.get(project.id)
        assert updated_project.visibility == "internal"

    def test__edit_project_settings_topics_default_no_topics_config(self, gl: Gitlab, project: Project) -> None:
        """
        Test that the topics are not changed when no topics are specified in the config
        """
        project.topics = ["topicA", "topicB"]
        project.save()

        config: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              visibility: internal
        """

        run_gitlabform(config, project)

        updated_project: Project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicA" in project_topics
        assert "topicB" in project_topics

    def test__edit_project_settings_topics_default(self, gl: Gitlab, project: Project) -> None:
        """
        Test that the topics are replaced when topics are specified in the config
        """
        project.topics = ["topicA", "topicB"]
        project.save()

        config: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - topicC
                - topicD
        """

        run_gitlabform(config, project)

        updated_project: Project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicC" in project_topics
        assert "topicD" in project_topics

    def test__edit_project_settings_topics_keep_existing_true(self, gl: Gitlab, project: Project) -> None:
        """
        Test that the existing topics are kept when keep_existing is true
        """
        project.topics = ["topicA", "topicB"]
        project.save()

        config: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - keep_existing: true
                - topicC
                - topicD
        """

        run_gitlabform(config, project)

        updated_project: Project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 4
        assert "topicA" in project_topics
        assert "topicB" in project_topics
        assert "topicC" in project_topics
        assert "topicD" in project_topics

    def test__edit_project_settings_topics_keep_existing_false(self, gl: Gitlab, project: Project) -> None:
        """
        Test that the existing topics are not kept when keep_existing is false
        """
        project.topics = ["topicA", "topicB"]
        project.save()

        config: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - keep_existing: false
                - topicC
                - topicD
        """

        run_gitlabform(config, project)

        updated_project: Project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicC" in project_topics
        assert "topicD" in project_topics

    def test__edit_project_settings_topics_delete(self, gl: Gitlab, project: Project) -> None:
        """
        Test that the existing topics are deleted when delete is true
        """
        project.topics = ["topicA", "topicB"]
        project.save()

        config: str = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              topics:
                - keep_existing: true
                - topicA:
                    delete: true
                - topicC
                - topicD:
                    delete: false
        """

        run_gitlabform(config, project)

        updated_project: Project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 3
        assert "topicB" in project_topics
        assert "topicC" in project_topics
        assert "topicD" in project_topics
