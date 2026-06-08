from unittest.mock import MagicMock

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    UserTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_protected_environments() -> None:
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          foo:
            name: foo
            deploy_access_levels:
              - access_level: maintainer
                group_inheritance_type: 0
              - user: jsmith
              - user_id: 123
              - user: bdoe
              - user_id: 456
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    gitlab_mock._get_user_id = MagicMock(side_effect=[78, 89])

    transformer = UserTransformer(gitlab_mock)
    transformer.transform(configuration)

    assert gitlab_mock._get_user_id.call_count == 2

    expected_transformed_config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          foo:
            name: foo
            deploy_access_levels:
              - access_level: maintainer
                group_inheritance_type: 0
              - user_id: 78
              - user_id: 123
              - user_id: 89
              - user_id: 456
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    assert configuration.config == expected_transformed_config.config


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            users: # this comment is needed...
              - a_user
    """
    configuration = Configuration(config_string=config_yaml)

    gitlab_mock = MagicMock(GitLab)
    gitlab_mock._get_user_id = MagicMock(side_effect=[123])

    transformer = UserTransformer(gitlab_mock)
    transformer.transform(configuration, last=True)

    assert gitlab_mock._get_user_id.call_count == 1

    expected_transformed_config_yaml = """
    projects_and_groups:
      "foo/bar":
        merge_requests_approval_rules:
          dev-uat:
            approvals_required: 1
            name: "Dev Code Review - UAT"
            user_ids: # this comment is needed...
              - 123
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)
    assert configuration.config == expected_transformed_config.config
