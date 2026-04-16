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


def test__transform_with_non_dict_value():
    """Test ImplicitNameTransformer skips non-dict/CommentedMap nodes."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        protected_environments:
          production:
            deploy_access_levels:
              - access_level: maintainer
          staging: some_string_value
          testing: 12345
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    # Should not raise any exceptions
    transformer.transform(configuration)

    # Check that production got a name field
    production = configuration.config["projects_and_groups"]["foo/bar"]["protected_environments"]["production"]
    assert production["name"] == "production"

    # staging should remain a string (not converted to dict with name field)
    staging = configuration.config["projects_and_groups"]["foo/bar"]["protected_environments"]["staging"]
    assert staging == "some_string_value"

    # testing should remain a number
    testing = configuration.config["projects_and_groups"]["foo/bar"]["protected_environments"]["testing"]
    assert testing == 12345


def test__transform_with_empty_protected_environments():
    """Test ImplicitNameTransformer handles empty protected_environments section."""
    config_yaml = """
    projects_and_groups:
      "foo/bar":
        settings:
          description: "A test project"
    """
    configuration = Configuration(config_string=config_yaml)

    transformer = ImplicitNameTransformer(MagicMock(GitLab))
    # Should not raise any exceptions
    transformer.transform(configuration)

    # Configuration should remain unchanged
    assert configuration.config["projects_and_groups"]["foo/bar"]["settings"]["description"] == "A test project"
