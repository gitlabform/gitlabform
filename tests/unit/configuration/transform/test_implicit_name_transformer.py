from unittest.mock import MagicMock

from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import (
    ImplicitNameTransformer,
)
from gitlabform.gitlab import GitLab

_base_cfg = f"""
    projects_and_groups:
      "foo/bar":
        protected_environments:
          enforce: true
          foo:
            deploy_access_levels:
              - access_level: 40
    """


def test__transform_for_protected_environments():
    configuration = Configuration(config_string=_base_cfg)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    expected_transformed_config_yaml = f"""
    {_base_cfg}
            name: foo
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    assert configuration.config == expected_transformed_config.config


def test__transform_for_protected_environments_sanity_check():
    configuration = Configuration(config_string=_base_cfg)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    expected_transformed_config_yaml = f"""
    {_base_cfg}
            name: blah
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    assert configuration.config != expected_transformed_config.config


def test__transform_for_group_protected_environments():
    group_cfg = """
    projects_and_groups:
      "foo/*":
        group_protected_environments:
          enforce: true
          production:
            deploy_access_levels:
              - access_level: 40
          custom_label:
            name: staging
            deploy_access_levels:
              - access_level: 30
    """
    configuration = Configuration(config_string=group_cfg)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    expected_yaml = """
    projects_and_groups:
      "foo/*":
        group_protected_environments:
          enforce: true
          production:
            deploy_access_levels:
              - access_level: 40
            name: production
          custom_label:
            name: staging
            deploy_access_levels:
              - access_level: 30
    """
    expected_transformed_config = Configuration(config_string=expected_yaml)

    assert configuration.config == expected_transformed_config.config
