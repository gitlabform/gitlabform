from unittest.mock import MagicMock

import pytest
from gitlab import GitlabGetError

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import PrincipalIdsTransformer


def _get_user_id(username: str) -> int | None:
    return {"user1": 101, "user2": 102}.get(username)


def _get_group_id(groupname: str) -> int:
    return {"group/a": 201, "team/dev": 202}[groupname]


def test__transform__users_and_groups_to_ids_in_multiple_sections():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          sec-review:
            approvals_required: 1
            users:
              - user1
              - user2
            groups:
              - group/a
          enforce: true

        protected_environments:
          production:
            deploy_access_levels:
              - user: user1
              - group: group/a

        branches:
          main:
            protected: true
            allowed_to_push:
              - user: user2
              - group: team/dev
            allowed_to_merge:
              - access_level: 40
            allowed_to_unprotect:
              - user_id: 77

        tags:
          v*:
            protected: true
            allowed_to_create:
              - user: user1
              - group: team/dev
              - user_id: 999
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_user_id_cached.side_effect = _get_user_id
    gitlab.get_group_id.side_effect = _get_group_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    rule = configuration.config["projects_and_groups"]["foo/bar"]["merge_requests_approval_rules"]["sec-review"]
    assert "users" not in rule
    assert "groups" not in rule
    assert rule["user_ids"] == [101, 102]
    assert rule["group_ids"] == [201]

    deploy_access_levels = configuration.config["projects_and_groups"]["foo/bar"]["protected_environments"][
        "production"
    ]["deploy_access_levels"]
    assert deploy_access_levels == [{"user_id": 101}, {"group_id": 201}]

    allowed_to_push = configuration.config["projects_and_groups"]["foo/bar"]["branches"]["main"]["allowed_to_push"]
    assert allowed_to_push == [{"user_id": 102}, {"group_id": 202}]

    allowed_to_create = configuration.config["projects_and_groups"]["foo/bar"]["tags"]["v*"]["allowed_to_create"]
    assert allowed_to_create == [{"user_id": 101}, {"group_id": 202}, {"user_id": 999}]


def test__transform__keeps_existing_ids_and_dedupes_when_users_are_also_set():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          sec-review:
            approvals_required: 1
            users:
              - user1
              - user2
            user_ids:
              - 999
              - 101
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_user_id_cached.side_effect = _get_user_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    rule = configuration.config["projects_and_groups"]["foo/bar"]["merge_requests_approval_rules"]["sec-review"]
    assert "users" not in rule
    assert rule["user_ids"] == [999, 101, 102]


def test__transform__raises_for_missing_user():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          sec-review:
            approvals_required: 1
            users:
              - missing-user
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_user_id_cached.return_value = None

    transformer = PrincipalIdsTransformer(gitlab)

    with pytest.raises(GitlabGetError, match="No users found when searching for username 'missing-user'"):
        transformer.transform(configuration)


def test__transform__injects_user_id_into_members_users_dict_keys():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        members:
          users:
            user1:
              access_level: 30
            user2:
              access_level: 40
              expires_at: 2026-01-01
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_user_id_cached.side_effect = _get_user_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    users = configuration.config["projects_and_groups"]["foo/bar"]["members"]["users"]
    assert users["user1"]["user_id"] == 101
    assert users["user1"]["access_level"] == 30
    assert users["user2"]["user_id"] == 102
    assert users["user2"]["access_level"] == 40


def test__transform__injects_group_id_into_members_groups_dict_keys():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        members:
          groups:
            group/a:
              group_access: 30
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_group_id.side_effect = _get_group_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    groups = configuration.config["projects_and_groups"]["foo/bar"]["members"]["groups"]
    assert groups["group/a"]["group_id"] == 201
    assert groups["group/a"]["group_access"] == 30


def test__transform__injects_user_id_into_group_members_users_dict_keys():
    config_yaml = """
    projects_and_groups:
      "my-group":
        group_members:
          users:
            user1:
              access_level: 50
            user2:
              access_level: 30
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_user_id_cached.side_effect = _get_user_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    users = configuration.config["projects_and_groups"]["my-group"]["group_members"]["users"]
    assert users["user1"]["user_id"] == 101
    assert users["user2"]["user_id"] == 102


def test__transform__injects_group_id_into_group_members_groups_dict_keys():
    config_yaml = """
    projects_and_groups:
      "my-group":
        group_members:
          groups:
            group/a:
              group_access: 30
            team/dev:
              group_access: 40
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    gitlab.get_group_id.side_effect = _get_group_id

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    groups = configuration.config["projects_and_groups"]["my-group"]["group_members"]["groups"]
    assert groups["group/a"]["group_id"] == 201
    assert groups["team/dev"]["group_id"] == 202


def test__transform__skips_dict_key_when_id_already_present():
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        members:
          users:
            user1:
              access_level: 30
              user_id: 999
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab = MagicMock()
    # get_user_id_cached should NOT be called since user_id already present
    gitlab.get_user_id_cached.side_effect = AssertionError("should not be called")

    transformer = PrincipalIdsTransformer(gitlab)
    transformer.transform(configuration)

    users = configuration.config["projects_and_groups"]["foo/bar"]["members"]["users"]
    assert users["user1"]["user_id"] == 999
