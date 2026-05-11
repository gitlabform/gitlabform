import pytest

from gitlabform.configuration import Configuration


@pytest.fixture
def configuration_with_bare_group_key():
    config_yaml = """
    ---
    projects_and_groups:
      some_group:
        group_settings:
          description: foo
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_both_bare_and_wildcard_keys():
    config_yaml = """
    ---
    projects_and_groups:
      bare_group:
        group_settings:
          description: from_bare
      wildcard_group/*:
        group_settings:
          description: from_wildcard
    """
    return Configuration(config_string=config_yaml)


def test_get_groups_recognizes_bare_top_level_group(configuration_with_bare_group_key):
    assert configuration_with_bare_group_key.get_groups() == ["some_group"]


def test_get_effective_config_for_bare_top_level_group(configuration_with_bare_group_key):
    effective_config = configuration_with_bare_group_key.get_effective_config_for_group("some_group")

    assert effective_config["group_settings"]["description"] == "foo"


def test_get_groups_recognizes_both_bare_and_wildcard_keys(configuration_with_both_bare_and_wildcard_keys):
    assert configuration_with_both_bare_and_wildcard_keys.get_groups() == ["bare_group", "wildcard_group"]


def test_wildcard_config_takes_precedence_over_bare_when_both_exist():
    config_yaml = """
    ---
    projects_and_groups:
      some_group:
        group_settings:
          description: from_bare
      some_group/*:
        group_settings:
          description: from_wildcard
    """
    configuration = Configuration(config_string=config_yaml)

    effective_config = configuration.get_effective_config_for_group("some_group")
    assert effective_config["group_settings"]["description"] == "from_wildcard"
