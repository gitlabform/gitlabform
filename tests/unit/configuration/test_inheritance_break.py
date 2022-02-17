import logging
import pytest

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_invalid_inheritance_break_at_common_level():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        secret_variables:
          inherit: false
          first:
            key: foo
            value: bar

      "some_group/my_project":
        secret_variables:
          second:
            key: bizz
            value: buzz
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_multiple_levels_for_my_project():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        secret_variables:
          third:
            key: foo
            value: bar

      "some_group/*":
        secret_variables:
          first:
            key: foo
            value: bar

      "some_group/my_project":
        secret_variables:
          inherit: false
          second:
            key: foo
            value: bar
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_group_level_for_my_project():
    config_yaml = """
    ---
    projects_and_groups:
      "some_group/*":
        secret_variables:
          first:
            key: foo
            value: bar

      "some_group/my_project":
        secret_variables:
          inherit: false
          second:
            key: bar
            value: foo

      "some_group/my_other_project":
        secret_variables:
          inherit: false
          third:
            key: biz
            value: buzz
    """
    return Configuration(config_string=config_yaml)


# break inheritance from one level - group level
def test__get_effective_config_for_my_project__with_group_level(
    configuration_with_group_level_for_my_project,
):
    effective_config = (
        configuration_with_group_level_for_my_project.get_effective_config_for_project(
            "some_group/my_project"
        )
    )

    secret_variables = effective_config["secret_variables"]

    assert secret_variables == {"second": {"key": "bar", "value": "foo"}}


# break inheritance from multiple levels - common level and group level
def test__get_effective_config_for_my_project__with_multiple_levels(
    configuration_with_multiple_levels_for_my_project,
):
    effective_config = configuration_with_multiple_levels_for_my_project.get_effective_config_for_project(
        "some_group/my_project"
    )

    secret_variables = effective_config["secret_variables"]

    assert secret_variables == {"second": {"key": "foo", "value": "bar"}}


# invalid inheritance at common level
def test__get_effective_config_for_project__with_invalid_inheritance_break(
    configuration_with_invalid_inheritance_break_at_common_level,
):

    with pytest.raises(SystemExit) as exception:
        configuration_with_invalid_inheritance_break_at_common_level.get_effective_config_for_project(
            "some_group/my_project"
        )
    assert exception.type == SystemExit
    assert exception.value.code == 1
