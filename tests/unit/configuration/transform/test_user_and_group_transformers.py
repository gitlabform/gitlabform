import ez_yaml
from deepdiff import DeepDiff
from pprint import pprint
from unittest.mock import MagicMock, patch

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    ConfigurationTransformers,
    UserTransformer,
    GroupTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = f"""
    projects_and_groups:

      "*":
        merge_requests_approval_rules:
          standard:
            approvals_required: 1
            name: "All eligible users"

      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            groups:
              - some_group
            users:
              - a_user
    """

    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    # Mock the python-gitlab wrapper for user transformer
    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_user_id_cached = MagicMock(side_effect=[2])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        ut = UserTransformer(gitlab_mock)
        ut.transform(configuration)

    # Mock the python-gitlab wrapper for group transformer
    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock(side_effect=[1])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        gt = GroupTransformer(gitlab_mock)
        gt.transform(configuration, last=True)

    # ut = UserTransformer(gitlab_mock)
    # ut.transform(configuration)

    effective_config_yaml_str = ez_yaml.to_string(obj=configuration.config, options={})
    print("!!!BEFORE:")
    print(effective_config_yaml_str)

    expected_transformed_config_yaml = f"""
    projects_and_groups:

      "*":
        merge_requests_approval_rules:
          standard:
            approvals_required: 1
            name: "All eligible users"

      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            group_ids:
              - 1
            user_ids:
              - 2
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    ut.convert_to_simple_types(expected_transformed_config)

    effective_config_yaml_str = ez_yaml.to_string(obj=expected_transformed_config.config, options={})
    print("!!!After:")
    print(effective_config_yaml_str)

    difference = DeepDiff(configuration.config, expected_transformed_config.config)
    assert not difference


def test__configuration_transformers_initialization():
    """Test that ConfigurationTransformers initializes all transformers."""
    gitlab_mock = MagicMock(GitLab)
    gitlab_mock.session = MagicMock()  # Add session attribute for GitlabWrapper

    with patch("gitlabform.configuration.transform.GitlabWrapper"):
        transformers = ConfigurationTransformers(gitlab_mock)

        from gitlabform.configuration.transform import (
            MergeRequestApprovalsTransformer,
            ImplicitNameTransformer,
            AccessLevelsTransformer,
        )

        assert isinstance(transformers.merge_request_approvals_transformer, MergeRequestApprovalsTransformer)
        assert isinstance(transformers.user_transformer, UserTransformer)
        assert isinstance(transformers.group_transformer, GroupTransformer)
        assert isinstance(transformers.implicit_name_transformer, ImplicitNameTransformer)
        assert isinstance(transformers.access_level_transformer, AccessLevelsTransformer)


def test__configuration_transformers_full_pipeline():
    """Test the full transform pipeline with ConfigurationTransformers."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          production:
            deploy_access_levels:
              - user: jsmith
              - access_level: maintainer
        merge_requests_approval_rules:
          dev-review:
            approvals_required: 2
            users:
              - alice
              - bob
            groups:
              - dev-team
        branches:
          main:
            protected: true
            push_access_level: no access
            merge_access_level: developer
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        # Mock user IDs: jsmith=100, alice=200, bob=300
        gl_mock.get_user_id_cached = MagicMock(side_effect=[100, 200, 300])
        # Mock group ID: dev-team=400
        gl_mock.get_group_id = MagicMock(side_effect=[400])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformers = ConfigurationTransformers(gitlab_mock)
        transformers.transform(configuration)

        # Verify transformations occurred
        config = configuration.config

        # Check user transformation for protected environments
        protected_env = config["projects_and_groups"]["foo/bar"]["protected_environments"]["production"]
        assert protected_env["deploy_access_levels"][0]["user_id"] == 100
        assert "user" not in protected_env["deploy_access_levels"][0]

        # Check user and group transformation for merge request approval rules
        approval_rule = config["projects_and_groups"]["foo/bar"]["merge_requests_approval_rules"]["dev-review"]
        assert approval_rule["user_ids"] == [200, 300]
        assert "users" not in approval_rule
        assert approval_rule["group_ids"] == [400]
        assert "groups" not in approval_rule

        # Check access level transformation
        branches = config["projects_and_groups"]["foo/bar"]["branches"]["main"]
        assert branches["push_access_level"] == 0
        assert branches["merge_access_level"] == 30

        # Check implicit name transformation
        assert protected_env["name"] == "production"


def test__configuration_transformers_with_old_merge_requests_syntax():
    """Test that ConfigurationTransformers handles old merge_requests syntax first."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests:
          approvals:
            approvals_before_merge: 1
          approvers:
            - user1
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_user_id_cached = MagicMock(side_effect=[123])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformers = ConfigurationTransformers(gitlab_mock)
        transformers.transform(configuration)

        # Old syntax should be converted first, then users transformed
        assert "merge_requests" not in configuration.config["projects_and_groups"]["foo/bar"]
        assert "merge_requests_approval_rules" in configuration.config["projects_and_groups"]["foo/bar"]

        approval_rule = configuration.config["projects_and_groups"]["foo/bar"]["merge_requests_approval_rules"][
            "legacy"
        ]
        assert approval_rule["user_ids"] == [123]
        assert "users" not in approval_rule


def test__configuration_transformers_with_empty_config():
    """Test that ConfigurationTransformers handles empty configuration gracefully."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        settings:
          description: "A test project"
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_user_id_cached = MagicMock(return_value=None)
        gl_mock.get_group_id = MagicMock(return_value=None)
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformers = ConfigurationTransformers(gitlab_mock)
        # Should not raise any exceptions
        transformers.transform(configuration)

        # Configuration should remain unchanged
        assert configuration.config["projects_and_groups"]["foo/bar"]["settings"]["description"] == "A test project"
