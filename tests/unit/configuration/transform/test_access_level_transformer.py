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
    ImplicitNameTransformer,
    MergeRequestApprovalsTransformer,
)
from gitlabform.gitlab import GitLab


def test__config__with_access_level_names__branches():
    config_yaml = f"""
    projects_and_groups:
      foobar/*:
        branches:
          develop:
            protected: false
          main:
            protected: true
            push_access_level: no access
            merge_access_level: developer
            unprotect_access_level: maintainer
            code_owner_approval_required: true
          branch_protected_from_changes:
            protected: true
            push_access_level: no access
            merge_access_level: no access
            unprotect_access_level: maintainer
      "*":
        branches:
          '*-something':
            protected: true
            push_access_level: no access
            merge_access_level: developer
            unprotect_access_level: maintainer
          allow_to_force_push:
            protected: true
            push_access_level: developer
            merge_access_level: developer
            unprotect_access_level: maintainer
            allow_force_push: true
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    config_with_numbers = f"""
    projects_and_groups:
      foobar/*:
        branches:
          develop:
            protected: false
          main:
            protected: true
            push_access_level: 0
            merge_access_level: 30
            unprotect_access_level: 40
            code_owner_approval_required: true
          branch_protected_from_changes:
            protected: true
            push_access_level: 0
            merge_access_level: 0
            unprotect_access_level: 40
      "*":
        branches:
          '*-something':
            protected: true
            push_access_level: 0
            merge_access_level: 30
            unprotect_access_level: 40
          allow_to_force_push:
            protected: true
            push_access_level: 30
            merge_access_level: 30
            unprotect_access_level: 40
            allow_force_push: true
    """
    configuration_with_numbers = Configuration(config_string=config_with_numbers)

    ddiff = DeepDiff(configuration.config, configuration_with_numbers.config)
    assert not ddiff


def test__config__with_access_level_names__group_ldap_links():
    config_yaml = f"""
    projects_and_groups:
      foobar/*:
        group_ldap_links:
          # "provider" field should contain a value that you can find in the GitLab web UI,
          # see https://github.com/gitlabform/gitlabform/issues/261
          devops_are_maintainers:
            provider: "AD"
            cn: "devops"
            group_access: maintainer
          developers_are_developers:
            provider: "AD"
            filter: "(employeeType=developer)"
            group_access: developer
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    config_with_numbers = f"""
    projects_and_groups:
      foobar/*:
        group_ldap_links:
          # "provider" field should contain a value that you can find in the GitLab web UI,
          # see https://github.com/gitlabform/gitlabform/issues/261
          devops_are_maintainers:
            provider: "AD"
            cn: "devops"
            group_access: 40
          developers_are_developers:
            provider: "AD"
            filter: "(employeeType=developer)"
            group_access: 30
    """
    configuration_with_numbers = Configuration(config_string=config_with_numbers)

    ddiff = DeepDiff(configuration.config, configuration_with_numbers.config)
    assert not ddiff


def test__config__with_access_level_names__branches_premium_syntax():
    config_yaml = f"""
    projects_and_groups:
      foobar/*:
        branches:
          special:
            protected: true
            allowed_to_push:
              - user: jsmith # you can use usernames...
              - user: bdoe
              - group: another-group # ...or group names (paths)...
            allowed_to_merge:
              - user_id: 15 # ...or user ids, if you know them...
              - access_level: developer # ...or the whole access levels, like in the other syntax
              - group_id: 456 # ...or group ids, if you know them...
            allowed_to_unprotect:
              - access_level: maintainer # ...or the whole access levels, like in the other syntax
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    config_with_numbers = f"""
    projects_and_groups:
      foobar/*:
        branches:
          special:
            protected: true
            allowed_to_push:
              - user: jsmith # you can use usernames...
              - user: bdoe
              - group: another-group # ...or group names (paths)...
            allowed_to_merge:
              - user_id: 15 # ...or user ids, if you know them...
              - access_level: 30 # ...or the whole access levels, like in the other syntax
              - group_id: 456 # ...or group ids, if you know them...
            allowed_to_unprotect:
              - access_level: 40 # ...or the whole access levels, like in the other syntax
    """
    configuration_with_numbers = Configuration(config_string=config_with_numbers)

    ddiff = DeepDiff(configuration.config, configuration_with_numbers.config)
    assert not ddiff


def test__config__with_access_level_names__invalid_name():
    config_yaml = f"""
    projects_and_groups:
      foobar/*:
        branches:
          special:
            protected: true
            allowed_to_push:
              - user: jsmith # you can use usernames...
              - user: bdoe
              - group: another-group # ...or group names (paths)...
            allowed_to_merge:
              - user_id: 15 # ...or user ids, if you know them...
              - access_level: developers # <-------------------------- this is invalid, it's plural
              - group_id: 456 # ...or group ids, if you know them...
            allowed_to_unprotect:
              - access_level: maintainer # ...or the whole access levels, like in the other syntax
    """
    configuration = Configuration(config_string=config_yaml)
    transformer = AccessLevelsTransformer(MagicMock(GitLab))

    with pytest.raises(SystemExit) as e:
        transformer.transform(configuration)

    assert e.value.code == EXIT_INVALID_INPUT


def test__config__with_access_level_names__invalid_in_branches():
    """Test AccessLevelsTransformer raises SystemExit for invalid access level in branches."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        branches:
          main:
            protected: true
            push_access_level: invalid_level
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))

    with pytest.raises(SystemExit) as e:
        transformer.transform(configuration)

    assert e.value.code == EXIT_INVALID_INPUT


def test__config__with_access_level_names__tags():
    """Test AccessLevelsTransformer transforms access levels for tags."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        tags:
          v*:
            protected: true
            create_access_level: maintainer
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    config_with_numbers = """
    projects_and_groups:
      "foo/bar":
        tags:
          v*:
            protected: true
            create_access_level: 40
    """
    configuration_with_numbers = Configuration(config_string=config_with_numbers)

    assert not DeepDiff(configuration.config, configuration_with_numbers.config)


def test__config__with_access_level_names__members():
    """Test AccessLevelsTransformer transforms access levels for members."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        members:
          users:
            alice:
              access_level: developer
            bob:
              access_level: maintainer
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    config_with_numbers = """
    projects_and_groups:
      "foo/bar":
        members:
          users:
            alice:
              access_level: 30
            bob:
              access_level: 40
    """
    configuration_with_numbers = Configuration(config_string=config_with_numbers)

    assert not DeepDiff(configuration.config, configuration_with_numbers.config)


def test__config__with_last_parameter():
    """Test that convert_to_simple_types is called when last=True."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        branches:
          main:
            protected: true
            push_access_level: maintainer
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = AccessLevelsTransformer(MagicMock(GitLab))

    # Transform with last=True to trigger convert_to_simple_types
    transformer.transform(configuration, last=True)

    # After conversion, should be simple dict types
    assert type(configuration.config) == dict
    assert type(configuration.config["projects_and_groups"]) == dict
