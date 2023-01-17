from unittest import TestCase

import ez_yaml
import pytest
from deepdiff import DeepDiff
from unittest.mock import MagicMock

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


#
# TODO: remove below test(s) in v4.x
#


def test__config__with_merge_request_approvals__many_users_and_groups_and_remove():
    config_before = f"""
    projects_and_groups:
      foobar/*:
        merge_requests:
          approvals:
            approvals_before_merge: 2
            reset_approvals_on_push: true
            disable_overriding_approvers_per_merge_request: true
          approvers:
            - user1
            - user2
          approver_groups:
            - my-group
            - my-group1/subgroup
            - my-group2/subgroup/subsubgroup
          remove_other_approval_rules: true
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      foobar/*:
        merge_requests_approvals:
          reset_approvals_on_push: true
          disable_overriding_approvers_per_merge_request: true
        merge_requests_approval_rules:
          legacy:
            approvals_required: 2
            name: {APPROVAL_RULE_NAME}
            users:
              - user1
              - user2
            groups:
              - my-group
              - my-group1/subgroup
              - my-group2/subgroup/subsubgroup
          enforce: true
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after


def test__config__with_merge_request_approvals__single_user_no_remove():
    config_before = f"""
    projects_and_groups:
      '*':
        merge_requests:
          approvals:
            approvals_before_merge: 2
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: false
          approvers:
            - user1
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      '*':
        merge_requests_approvals:
          reset_approvals_on_push: false
          disable_overriding_approvers_per_merge_request: false
        merge_requests_approval_rules:
          legacy:
            approvals_required: 2
            name: {APPROVAL_RULE_NAME}
            users:
              - user1
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after


def test__config__with_merge_request_approvals__single_group_no_remove():
    config_before = f"""
    projects_and_groups:
      'foo/bar':
        merge_requests:
          approvals:
            approvals_before_merge: 1
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: true
          approver_groups:
            - my-group2
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      'foo/bar':
        merge_requests_approvals:
          reset_approvals_on_push: false
          disable_overriding_approvers_per_merge_request: true
        merge_requests_approval_rules:
          legacy:
            approvals_required: 1
            name: {APPROVAL_RULE_NAME}
            groups:
              - my-group2
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after


def test__config__with_merge_request_approvals__guessing_approvals_before_merge():
    config_before = f"""
    projects_and_groups:
      'foo/bar':
        merge_requests:
          approvals:
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: true
          approver_groups:
            - my-group2
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      'foo/bar':
        merge_requests_approvals:
          reset_approvals_on_push: false
          disable_overriding_approvers_per_merge_request: true
        merge_requests_approval_rules:
          legacy:
            approvals_required: 2
            name: {APPROVAL_RULE_NAME}
            groups:
              - my-group2
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after


def test__config__with_merge_request_approvals__inheritance_1():
    config_before = f"""
    projects_and_groups:
      group/*:
        merge_requests:
          approvals:
            approvals_before_merge: 2
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: true
            merge_requests_author_approval: false
          approvers:
            - user1
            - user2
          approver_groups:
            - some-group

      group/envs/qa:
        merge_requests:
          approvals:
            approvals_before_merge: 0
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      group/*:
        merge_requests_approvals:
          reset_approvals_on_push: false
          disable_overriding_approvers_per_merge_request: true
          merge_requests_author_approval: false
        merge_requests_approval_rules:
          legacy:
            approvals_required: 2
            name: {APPROVAL_RULE_NAME}
            users:
              - user1
              - user2
            groups:
              - some-group

      group/envs/qa:
        merge_requests_approval_rules:
          legacy:
            approvals_required: 0
            name: {APPROVAL_RULE_NAME}
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after


def test__config__with_merge_request_approvals__inheritance_2():
    config_before = f"""
    projects_and_groups:
      group/*:
        merge_requests:
          approvals:
            approvals_before_merge: 0

      group/envs/qa:
        merge_requests:
          approvals:
            approvals_before_merge: 2
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: true
            merge_requests_author_approval: false
          approvers:
            - user1
            - user2
          approver_groups:
            - some-group
    """
    config_before = Configuration(config_string=config_before)

    transformer = MergeRequestApprovalsTransformer(MagicMock(GitLab))
    transformer.transform(config_before)
    config_before = ez_yaml.to_string(obj=config_before.config, options={})

    config_after = f"""
    projects_and_groups:
      group/*:
        merge_requests_approval_rules:
          legacy:
            approvals_required: 0
            name: {APPROVAL_RULE_NAME}
      group/envs/qa:
        merge_requests_approvals:
          reset_approvals_on_push: false
          disable_overriding_approvers_per_merge_request: true
          merge_requests_author_approval: false
        merge_requests_approval_rules:
          legacy:
            approvals_required: 2
            name: {APPROVAL_RULE_NAME}
            users:
              - user1
              - user2
            groups:
              - some-group
    """
    config_after = Configuration(config_string=config_after)
    config_after = ez_yaml.to_string(obj=config_after.config, options={})

    assert config_before == config_after
