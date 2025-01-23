from typing import List
from tests.acceptance import run_gitlabform


class TestProjectTopics:
    def test__create_project_topics(self, gl, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_topics:
              topics:
                - topicA
                - topicB
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicA" in project_topics
        assert "topicB" in project_topics

    def test__update_project_topics(self, gl, project):
        project.topics = ["topicA", "topicB"]
        project.save()

        self.test__create_project_topics(gl, project)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_topics:
              topics:
                - topicA
                - topicB
                - topicC
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 3
        assert "topicA" in project_topics
        assert "topicB" in project_topics
        assert "topicC" in project_topics

    def test__delete_project_topics(self, gl, project):
        project.topics = ["topicA", "topicB"]
        project.save()

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_topics:
              topics:
                - topicA:
                    delete: true
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 1
        assert "topicB" in project_topics

    def test__enforce_project_topics(self, gl, project):
        project.topics = ["topicA", "topicB"]
        project.save()

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_topics:
              topics:
                - topicC
                - topicD
              enforce: true
        """

        run_gitlabform(config, project)

        updated_project = gl.projects.get(project.id)
        project_topics: List[str] = updated_project.topics

        assert len(project_topics) == 2
        assert "topicC" in project_topics
        assert "topicD" in project_topics
