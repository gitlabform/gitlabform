import pytest
import gitlab

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_tag_access_levels, run_gitlabform

pytestmark = pytest.mark.requires_license


class TestTags:
    def test__allowed_to_create_by_user_only(self, project, tag, make_user):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {user1.id}
                  - user: {user2.username}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted([AccessLevel.NO_ACCESS.value])
        assert allowed_to_create_access_user_ids == sorted([user1.id, user2.id])
        assert allowed_to_create_access_group_ids == []

    def test__allowed_to_create_by_user_but_without_explicit_role_config(self, project, tag, make_user):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - user_id: {user1.id}
                  - user: {user2.username}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == []
        assert allowed_to_create_access_user_ids == sorted([user1.id, user2.id])
        assert allowed_to_create_access_group_ids == []

    def test__allowed_to_create_by_user_and_role(self, project, tag, make_user):
        user1 = make_user(AccessLevel.DEVELOPER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user: {user1.username}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted(
            [
                AccessLevel.MAINTAINER.value,
            ]
        )
        assert allowed_to_create_access_user_ids == sorted([user1.id])
        assert allowed_to_create_access_group_ids == []

    def test__allowed_to_create_by_group_only(self, project, tag, group_to_invite_to_project):
        shared_group1 = group_to_invite_to_project(project, AccessLevel.DEVELOPER)
        shared_group2 = group_to_invite_to_project(project, AccessLevel.MAINTAINER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - group_id: {shared_group1.id}
                  - group: {shared_group2.name}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted(
            [
                AccessLevel.NO_ACCESS.value,
            ]
        )
        assert allowed_to_create_access_user_ids == []
        assert allowed_to_create_access_group_ids == sorted([shared_group1.id, shared_group2.id])

    def test__allowed_to_create_by_user_and_group_only(self, project, tag, make_user, group_to_invite_to_project):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)
        shared_group1 = group_to_invite_to_project(project, AccessLevel.DEVELOPER)
        shared_group2 = group_to_invite_to_project(project, AccessLevel.MAINTAINER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {user1.id}
                  - user: {user2.username}
                  - group_id: {shared_group1.id}
                  - group: {shared_group2.name}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted(
            [
                AccessLevel.NO_ACCESS.value,
            ]
        )
        assert allowed_to_create_access_user_ids == sorted([user1.id, user2.id])
        assert allowed_to_create_access_group_ids == sorted([shared_group1.id, shared_group2.id])

    def test__allowed_to_create_by_user_and_group_and_role(self, project, tag, make_user, group_to_invite_to_project):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)
        shared_group1 = group_to_invite_to_project(project, AccessLevel.DEVELOPER)
        shared_group2 = group_to_invite_to_project(project, AccessLevel.MAINTAINER)

        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.DEVELOPER.value}
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user_id: {user1.id}
                  - user: {user2.username}
                  - group_id: {shared_group1.id}
                  - group: {shared_group2.name}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted([AccessLevel.DEVELOPER.value, AccessLevel.MAINTAINER.value])
        assert allowed_to_create_access_user_ids == sorted([user1.id, user2.id])
        assert allowed_to_create_access_group_ids == sorted([shared_group1.id, shared_group2.id])

    def test__allowed_to_create_by_dev_role_only(self, project, tag):
        config_tag_protection_allowed_to_create = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                allowed_to_create:
                  - access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config_tag_protection_allowed_to_create, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted(
            [
                AccessLevel.DEVELOPER.value,
            ]
        )
        assert allowed_to_create_access_user_ids == []
        assert allowed_to_create_access_group_ids == []

    def test__access_level_role_by_mixed_config(self, project, tag):
        config_tag_protection_allowed_to_create_and_create_access_level = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              {tag}:
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
                allowed_to_create:
                  - access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config_tag_protection_allowed_to_create_and_create_access_level, project)
        (
            allowed_to_create_access_levels,
            allowed_to_create_access_user_ids,
            allowed_to_create_access_group_ids,
        ) = get_only_tag_access_levels(project, tag)

        assert allowed_to_create_access_levels == sorted([AccessLevel.DEVELOPER.value, AccessLevel.MAINTAINER.value])
        assert allowed_to_create_access_user_ids == []
        assert allowed_to_create_access_group_ids == []
