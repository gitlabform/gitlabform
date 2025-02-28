from deepdiff import DeepDiff
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

    assert not DeepDiff(configuration.config, expected_transformed_config.config)


def test__transform_for_protected_environments_sanity_check():
    configuration = Configuration(config_string=_base_cfg)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    transformer.transform(configuration)

    expected_transformed_config_yaml = f"""
    {_base_cfg}
            name: blah
    """

    expected_transformed_config = Configuration(config_string=expected_transformed_config_yaml)

    assert DeepDiff(configuration.config, expected_transformed_config.config)
