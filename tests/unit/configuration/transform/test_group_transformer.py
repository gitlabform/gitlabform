from unittest.mock import MagicMock

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
    gitlab_mock._get_group_id = MagicMock(side_effect=[123])

    transformer = GroupTransformer(gitlab_mock)
    transformer.transform(configuration, last=True)

    assert gitlab_mock._get_group_id.call_count == 1

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

    assert configuration.config == expected_transformed_config.config


def test__transform_for_group_protected_environments() -> None:
    config_yaml = """
    projects_and_groups:
      "foo/*":
        group_protected_environments:
          production:
            name: production
            deploy_access_levels:
              - group: foo/deployers
              - group_id: 100
            approval_rules:
              - group: foo/approvers
                required_approvals: 1
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    gitlab_mock._get_group_id = MagicMock(side_effect=[101, 102])

    transformer = GroupTransformer(gitlab_mock)
    transformer.transform(configuration, last=True)

    assert gitlab_mock._get_group_id.call_count == 2

    expected_transformed_config_yaml = """
    projects_and_groups:
      "foo/*":
        group_protected_environments:
          production:
            name: production
            deploy_access_levels:
              - group_id: 101
              - group_id: 100
            approval_rules:
              - required_approvals: 1
                group_id: 102
    """
    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    assert configuration.config == expected_transformed_config.config
