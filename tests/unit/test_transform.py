from unittest import TestCase
from unittest.mock import MagicMock

import pytest
from deepdiff import DeepDiff

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.transform import AccessLevelsTransformer, UserTransformer


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

    AccessLevelsTransformer.transform(configuration)

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

    AccessLevelsTransformer.transform(configuration)

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

    AccessLevelsTransformer.transform(configuration)

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

    with pytest.raises(SystemExit) as e:
        AccessLevelsTransformer.transform(configuration)
    assert e.value.code == EXIT_INVALID_INPUT


class TestUserTransformer(TestCase):
    def test__transform_for_protected_environments(self) -> None:
        config_yaml = f"""
        projects_and_groups:
          "foo/bar":
            protected_environments:
              foo:
                name: foo
                deploy_access_levels:
                  - access_level: 40
                    group_inheritance_type: 0
                  - user: jsmith
                  - user_id: 123
                  - user: bdoe
                  - user_id: 456
        """
        configuration = Configuration(config_string=config_yaml)

        gitlab_mock = MagicMock(GitLab)
        gitlab_mock._get_user_id = MagicMock(side_effect=[78, 89])

        UserTransformer.transform(configuration, gitlab_mock)

        assert gitlab_mock._get_user_id.call_count == 2

        expected_transformed_config_yaml = f"""
        projects_and_groups:
          "foo/bar":
            protected_environments:
              foo:
                name: foo
                deploy_access_levels:
                  - access_level: 40
                    group_inheritance_type: 0
                  - user_id: 78
                  - user_id: 123
                  - user_id: 89
                  - user_id: 456
        """

        expected_transformed_config = Configuration(
            config_string=expected_transformed_config_yaml
        )

        assert not DeepDiff(configuration.config, expected_transformed_config.config)
