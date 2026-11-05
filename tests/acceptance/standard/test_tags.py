import logging

import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)


@pytest.fixture(scope="function")
def tags(project):
    tag_names = [
        "tag1",
        "tag2",
        "tag3",
    ]
    tags = []

    for tag_name in tag_names:
        tag = project.tags.create({"tag_name": tag_name, "ref": "main"})
        tags.append(tag)

    yield tags

    protected_tags = project.protectedtags.list()
    for protected_tag in protected_tags:
        protected_tag.delete()

    for tag in tags:
        tag.delete()


class TestTags:
    def test__protect_single_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

    def test__protect_wildcard_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag*"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

    def test__unprotect_the_same_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag*"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: false
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 0

    def test__unprotect_unknown_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag_unknown":
                protected: false
        """

        # In strict mode, processor should exit immediately
        with pytest.raises(SystemExit):
            run_gitlabform(config, project)

    def test__keep_previous_protection_when_protect_fails(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, project)

        # GitLab does not accept the Owner role for protected tags
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.OWNER.value}
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, project)

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.DEVELOPER.value

    def test__keep_unchanged_protection(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)
        access_level_id = project.protectedtags.get("tag1").create_access_levels[0]["id"]

        run_gitlabform(config, project)

        assert project.protectedtags.get("tag1").create_access_levels[0]["id"] == access_level_id

    def test__show_protection_changes_in_dry_run(self, project, tags, caplog):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.DEVELOPER.value}
        """

        with caplog.at_level(logging.INFO):
            run_gitlabform(config, project, noop=True)

        assert "tags changes" in caplog.text
        assert f'"access_level": {AccessLevel.DEVELOPER.value}' in caplog.text
        protected_tag = project.protectedtags.get("tag1")
        assert protected_tag.create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

    def test__protect_single_tag_no_access(self, project, tags):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                tags:
                  tag1:
                    protected: true
                    create_access_level: {AccessLevel.NO_ACCESS.value}
            """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.NO_ACCESS.value

    def test__protect_single_tag_with_access_level_names(self, project, tags):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                tags:
                  tag1:
                    protected: true
                    create_access_level: maintainer
            """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value
