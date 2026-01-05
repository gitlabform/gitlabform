from unittest import TestCase

import ez_yaml
import pytest
from deepdiff import DeepDiff
from unittest.mock import MagicMock, patch

from gitlabform.constants import APPROVAL_RULE_NAME
from gitlabform import EXIT_INVALID_INPUT
from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    AccessLevelsTransformer,
    UserTransformer,
    ImplicitNameTransformer,
    MergeRequestApprovalsTransformer,
)
from gitlabform.gitlab import GitLab


def test__transform_for_protected_environments() -> None:
    config_yaml = f"""
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

    # Mock the python-gitlab wrapper
    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_user_id_cached = MagicMock(side_effect=[78, 89])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = UserTransformer(gitlab_mock)
        transformer.transform(configuration)

        assert gl_mock.get_user_id_cached.call_count == 2

    expected_transformed_config_yaml = f"""
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

    assert not DeepDiff(configuration.config, expected_transformed_config.config)


def test__transform_for_merge_request_approvals() -> None:
    config_yaml = f"""
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

    # Mock the python-gitlab wrapper
    with patch("gitlabform.configuration.transform.GitlabWrapper") as wrapper_mock:
        gl_mock = MagicMock()
        gl_mock.get_user_id_cached = MagicMock(side_effect=[123])
        wrapper_mock.return_value.get_gitlab.return_value = gl_mock

        transformer = UserTransformer(gitlab_mock)
        transformer.transform(configuration, last=True)

        assert gl_mock.get_user_id_cached.call_count == 1

    expected_transformed_config_yaml = f"""
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
    transformer.convert_to_simple_types(expected_transformed_config)

    assert not DeepDiff(configuration.config, expected_transformed_config.config)
