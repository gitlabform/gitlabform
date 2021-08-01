import pytest

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.configuration.projects_and_groups import ConfigurationProjectsAndGroups
from gitlabform.filter import NonEmptyConfigsProvider


def test_error_on_missing_key():
    config_yaml = """
    ---
    # no key at all
    """

    with pytest.raises(SystemExit) as e:
        configuration = ConfigurationProjectsAndGroups(config_string=config_yaml)
        NonEmptyConfigsProvider(configuration, None, None)
    assert e.value.code == EXIT_INVALID_INPUT


def test_error_on_empty_key():
    config_yaml = """
    ---
    projects_and_groups:
    """

    with pytest.raises(SystemExit) as e:
        configuration = ConfigurationProjectsAndGroups(config_string=config_yaml)
        NonEmptyConfigsProvider(configuration, None, None)
    assert e.value.code == EXIT_INVALID_INPUT
