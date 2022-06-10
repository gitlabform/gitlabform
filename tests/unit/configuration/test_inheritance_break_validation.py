import logging
import pytest

from gitlabform.configuration import Configuration
from gitlabform import EXIT_INVALID_INPUT

logger = logging.getLogger(__name__)


def test__get_effective_config_for_project__invalid_flag_set_at_common_level():
    config_yaml = """
        ---
        projects_and_groups:
          "*":
            inherit: false
            secret_variables:
              first:
                key: foo
                value: bar
        """

    configuration = Configuration(config_string=config_yaml).get_common_config()
    section_key = "*"
    with pytest.raises(SystemExit) as exception:
        Configuration.validate_break_inheritance_flag(configuration, section_key)
    assert exception.type == SystemExit
    assert exception.value.code == EXIT_INVALID_INPUT


def test__get_effective_config_for_project__invalid_flag_set_at_group_level():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        secret_variables:
          inherit: false
          first:
            key: foo
            value: bar
    """

    group_name = "some_group"
    configuration = Configuration(config_string=config_yaml).get_group_config(
        group_name
    )
    with pytest.raises(SystemExit) as exception:
        Configuration.validate_break_inheritance_flag(configuration, group_name)
    assert exception.type == SystemExit
    assert exception.value.code == EXIT_INVALID_INPUT


def test__get_effective_config_for_project__invalid_flag_set_at_project_level():
    config_yaml = """
    ---
    projects_and_groups:
      "some_group/some_project":
        secret_variables:
          inherit: false
          foo: bar
    """

    group_and_project_name = "some_group/some_project"
    configuration = Configuration(config_string=config_yaml).get_project_config(
        group_and_project_name
    )
    with pytest.raises(SystemExit) as exception:
        Configuration.validate_break_inheritance_flag(
            configuration, group_and_project_name
        )
    assert exception.type == SystemExit
    assert exception.value.code == EXIT_INVALID_INPUT
