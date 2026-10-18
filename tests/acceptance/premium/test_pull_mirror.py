import logging
import os
from typing import Generator

import pytest
from gitlab.exceptions import GitlabGetError
from gitlab.v4.objects import Group, Project

from gitlabform.processors.util.mirrors import (
    normalize_mirror_url_for_comparison as _normalize_url_for_comparison,
)
from tests.acceptance import run_gitlabform, get_random_name, create_project

pytestmark = pytest.mark.requires_license


@pytest.fixture(scope="class")
def mirror_source_project(other_group: Group) -> Generator[Project, None, None]:
    """Create a source project in another group to pull from."""
    project = create_project(other_group, get_random_name("pull_mirror_source"))
    yield project
    project.delete()


@pytest.fixture(scope="class")
def mirror_source_url(mirror_source_project: Project, root_username: str, root_access_token: str) -> str:
    """HTTP URL with embedded credentials pointing to the source project."""
    gitlab_url = os.getenv("GITLAB_URL", "http://localhost").rstrip("/")
    base_url = gitlab_url.replace("http://", f"http://{root_username}:{root_access_token}@")
    return f"{base_url}/{mirror_source_project.path_with_namespace}.git"


class TestProjectPullMirrorProcessor:
    def test_pull_mirror_create(self, project: Project, mirror_source_url: str) -> None:
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            pull_mirror:
              url: {mirror_source_url}
              enabled: true
              mirror_trigger_builds: false
        """

        run_gitlabform(config, project.path_with_namespace)

        mirror = project.pull_mirror.get()
        assert mirror.enabled is True
        assert mirror.mirror_trigger_builds is False
        assert _normalize_url_for_comparison(mirror.url) == _normalize_url_for_comparison(mirror_source_url)

    def test_pull_mirror_unchanged(self, project: Project, mirror_source_url: str, caplog) -> None:
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            pull_mirror:
              url: {mirror_source_url}
              enabled: true
              mirror_trigger_builds: false
        """

        # First run to ensure the mirror exists with this config
        run_gitlabform(config, project.path_with_namespace)

        with caplog.at_level(logging.INFO):
            run_gitlabform(config, project.path_with_namespace)

        assert "Pull mirror remains unchanged" in caplog.text

    def test_pull_mirror_update(self, project: Project, mirror_source_url: str, caplog) -> None:
        # Ensure the mirror exists
        self.test_pull_mirror_create(project, mirror_source_url)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            pull_mirror:
              url: {mirror_source_url}
              enabled: true
              mirror_trigger_builds: true
        """

        with caplog.at_level(logging.INFO):
            run_gitlabform(config, project.path_with_namespace)

        assert "Updated pull mirror" in caplog.text

        mirror = project.pull_mirror.get()
        assert mirror.enabled is True
        assert mirror.mirror_trigger_builds is True

    def test_pull_mirror_disable(self, project: Project, mirror_source_url: str, caplog) -> None:
        # Ensure the mirror exists
        self.test_pull_mirror_create(project, mirror_source_url)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            pull_mirror:
              enabled: false
        """

        run_gitlabform(config, project.path_with_namespace)

        # after disabling, GitLab reports the project as not mirrored
        with pytest.raises(GitlabGetError) as e:
            project.pull_mirror.get()
        assert "not mirrored" in str(e.value)

        # a second disable run is idempotent: the mirror now looks absent,
        # and without a 'url' there is nothing to configure
        with caplog.at_level(logging.INFO):
            run_gitlabform(config, project.path_with_namespace)
        assert "Skip configuring pull mirror" in caplog.text

    def test_pull_mirror_force_pull(self, project_for_function: Project, mirror_source_url: str, caplog) -> None:
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            pull_mirror:
              url: {mirror_source_url}
              enabled: true
              force_pull: true
        """

        with caplog.at_level(logging.INFO):
            run_gitlabform(config, project_for_function.path_with_namespace)

        assert "Triggered pull mirror sync" in caplog.text

    def test_pull_mirror_create_error(self, project_for_function: Project, caplog) -> None:
        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            pull_mirror:
              url: invalid-scheme://invalid-url.com/repo.git
              enabled: true
        """

        with caplog.at_level(logging.WARNING):
            run_gitlabform(config, project_for_function.path_with_namespace)

        assert "Failed to create pull mirror" in caplog.text

        with pytest.raises(GitlabGetError):
            project_for_function.pull_mirror.get()
