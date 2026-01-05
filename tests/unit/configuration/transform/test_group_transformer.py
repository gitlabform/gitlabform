from deepdiff import DeepDiff
from unittest.mock import MagicMock, patch

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    GroupTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = f"""
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            groups: # this comment is needed...
              - a_group
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    # Mock the python-gitlab wrapper
    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock(side_effect=[123])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = GroupTransformer(gitlab_mock)
        transformer.transform(configuration, last=True)

        assert gl_mock.get_group_id.call_count == 1

    # effective_config_yaml_str = ez_yaml.to_string(obj=configuration.config, options={})
    # print("!!!")
    # print(effective_config_yaml_str)

    expected_transformed_config_yaml = f"""
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            group_ids: # this comment is needed...
              - 123
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)
    transformer.convert_to_simple_types(expected_transformed_config)

    assert not DeepDiff(configuration.config, expected_transformed_config.config)


def test__transform_for_protected_environments() -> None:
    """Test GroupTransformer transforms group names to IDs for protected environments."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          production:
            deploy_access_levels:
              - group: dev-team
              - access_level: maintainer
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock(return_value=999)
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = GroupTransformer(gitlab_mock)
        transformer.transform(configuration)

        deploy_access = configuration.config["projects_and_groups"]["foo/bar"]["protected_environments"]["production"][
            "deploy_access_levels"
        ]
        assert deploy_access[0]["group_id"] == 999
        assert "group" not in deploy_access[0]


def test__transform_for_multiple_groups() -> None:
    """Test GroupTransformer handles multiple groups in approval rules."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          security-review:
            approvals_required: 2
            groups:
              - security-team
              - compliance-team
              - audit-team
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock(side_effect=[111, 222, 333])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = GroupTransformer(gitlab_mock)
        transformer.transform(configuration)

        approval_rule = configuration.config["projects_and_groups"]["foo/bar"]["merge_requests_approval_rules"][
            "security-review"
        ]
        assert approval_rule["group_ids"] == [111, 222, 333]
        assert "groups" not in approval_rule
        assert gl_mock.get_group_id.call_count == 3


def test__transform_with_no_groups() -> None:
    """Test that GroupTransformer handles configuration with no group fields."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          production:
            deploy_access_levels:
              - access_level: maintainer
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)

    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_group_id = MagicMock()
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = GroupTransformer(gitlab_mock)
        transformer.transform(configuration)

        # Should not call get_group_id since no groups to transform
        assert gl_mock.get_group_id.call_count == 0
