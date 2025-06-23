import sys
import pytest
from tests.acceptance import (
    run_gitlabform,
)
from pathlib import Path
from ruamel.yaml import YAML
from gitlab.v4.objects import Project


class TestRunning:
    # noinspection PyPep8Naming
    def test__ALL(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          '*':
            project_settings:
              request_access_enabled: true
        """

        run_gitlabform(config, "ALL")

        project = gl.projects.get(project.id)
        assert project.request_access_enabled is True

        other_project = gl.projects.get(other_project.id)
        assert other_project.request_access_enabled is True

    def test__ALL_output_file(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          '*':
            project_settings:
              request_access_enabled: true
        """

        run_gitlabform(config, "ALL", output_file="output.yml")

        project = gl.projects.get(project.id)
        assert project.request_access_enabled is True

        other_project = gl.projects.get(other_project.id)
        assert other_project.request_access_enabled is True

        path = Path("output.yml")
        yaml = YAML(typ="safe")
        assert yaml.load(path)

    # noinspection PyPep8Naming
    def test__ALL_dry_run(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          '*':
            project_settings:
              request_access_enabled: false
        """

        run_gitlabform(config, "ALL", noop=True)

        project = gl.projects.get(project.id)
        assert project.request_access_enabled is True

        other_project = gl.projects.get(other_project.id)
        assert other_project.request_access_enabled is True

    # noinspection PyPep8Naming
    def test__ALL_DEFINED(self, gl, project, other_project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        run_gitlabform(config, "ALL_DEFINED")

        project = gl.projects.get(project.id)
        assert project.suggestion_commit_message == "foobar"

        project = gl.projects.get(other_project.id)
        assert project.suggestion_commit_message != "foobar"

        config = f"""
        projects_and_groups:
          non/existent_project:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, "ALL_DEFINED")

        config = f"""
        projects_and_groups:
          non_existent_group/*:
            project_settings:
              suggestion_commit_message: 'foobar'
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, "ALL_DEFINED")
