import logging
import pytest

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_invalid_inheritance_break_set_at_common_level():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        secret_variables:
          inherit: false
          first:
            key: foo
            value: bar
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_invalid_inheritance_break_set_at_group_level():
    config_yaml = """
    ---
    projects_and_groups:
      "some_group/*":
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
def configuration_with_invalid_inheritance_break_set_at_project_level():
    config_yaml = """
    ---
    projects_and_groups:
      "some_group/my_project":
        secret_variables:
          inherit: false
          second:
            key: bizz
            value: buzz
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_break_inheritance_from_multiple_levels_set_at_project_level():
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
            key: bizz
            value: buzz
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_break_inheritance_from_common_level_set_at_group_level():
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
def configuration_with_break_inheritance_from_common_level_set_at_project_level():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        secret_variables:
          third:
            key: foo
            value: bar

      "some_group/*":
        members:
          users:
            user1: developer
            user2: developer

      "some_group/my_project":
        secret_variables:
          inherit: false
          second:
            key: bizz
            value: buzz
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_break_inheritance_from_group_level_set_at_project_level():
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
            key: bizz
            value: buzz
        public_variables:
          key: fizz
          value: fuzz
    
      "some_group/my_other_project":
        secret_variables:
          fourth:
            key: foo4
            value: bar4
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_break_inheritance_from_common_and_group_level_set_at_group_and_project_level():
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
          inherit: false
          first:
            key: foo
            value: bar
        members:
          users:
            user1: developer
            user2: developer

      "some_group/my_project":
        secret_variables:
          second:
            key: bizz
            value: buzz
        members:
          inherit: false
          users:
            user3: maintainer
            user4: maintainer
    """
    return Configuration(config_string=config_yaml)


def test__get_effective_config_for_project__with_invalid_inheritance_break_set_at_common_level(
    configuration_with_invalid_inheritance_break_set_at_common_level,
):
    with pytest.raises(SystemExit) as exception:
        configuration_with_invalid_inheritance_break_set_at_common_level.get_effective_config_for_project(
            "another_group/another_project"
        )
    assert exception.type == SystemExit
    assert exception.value.code == 2


def test__get_effective_config_for_project__with_invalid_inheritance_break_set_at_group_level(
    configuration_with_invalid_inheritance_break_set_at_group_level,
):
    with pytest.raises(SystemExit) as exception:
        configuration_with_invalid_inheritance_break_set_at_group_level.get_effective_config_for_project(
            "some_group/my_project"
        )
    assert exception.type == SystemExit
    assert exception.value.code == 2


def test__get_effective_config_for_project__with_invalid_inheritance_break_set_at_project_level(
    configuration_with_invalid_inheritance_break_set_at_project_level,
):
    with pytest.raises(SystemExit) as exception:
        configuration_with_invalid_inheritance_break_set_at_project_level.get_effective_config_for_project(
            "some_group/my_project"
        )
    assert exception.type == SystemExit
    assert exception.value.code == 2


def test__get_effective_config_for_my_project__with_break_inheritance_from_multiple_levels_set_at_project_level(
    configuration_with_break_inheritance_from_multiple_levels_set_at_project_level,
):
    effective_config = configuration_with_break_inheritance_from_multiple_levels_set_at_project_level.get_effective_config_for_project(
        "some_group/my_project"
    )

    secret_variables = effective_config["secret_variables"]

    assert secret_variables == {
        "inherit": False,
        "second": {"key": "bizz", "value": "buzz"},
    }


def test__get_effective_config_for_my_project__with_break_inheritance_from_common_levels_set_at_group_level(
    configuration_with_break_inheritance_from_common_level_set_at_group_level,
):
    effective_config = configuration_with_break_inheritance_from_common_level_set_at_group_level.get_effective_config_for_project(
        "some_group/my_project"
    )

    secret_variables = effective_config["secret_variables"]

    assert secret_variables == {
        "first": {"key": "foo", "value": "bar"},
        "inherit": False,
        "second": {"key": "bizz", "value": "buzz"},
    }


def test__get_effective_config_for_my_project__with_break_inheritance_from_common_levels_set_at_project_level(
    configuration_with_break_inheritance_from_common_level_set_at_project_level,
):
    effective_config = configuration_with_break_inheritance_from_common_level_set_at_project_level.get_effective_config_for_project(
        "some_group/my_project"
    )

    assert effective_config == {
        "members": {
            "users": {
                "user1": "developer",
                "user2": "developer",
            }
        },
        "secret_variables": {
            "inherit": False,
            "second": {"key": "bizz", "value": "buzz"},
        },
    }


def test__get_effective_config_for_my_project__with_break_inheritance_from_group_level_set_at_project_level(
    configuration_with_break_inheritance_from_group_level_set_at_project_level,
):
    effective_config = configuration_with_break_inheritance_from_group_level_set_at_project_level.get_effective_config_for_project(
        "some_group/my_project"
    )

    assert effective_config == {
        "secret_variables": {
            "inherit": False,
            "second": {"key": "bizz", "value": "buzz"},
        },
        "public_variables": {"key": "fizz", "value": "fuzz"},
    }


def test__get_effective_config_for_my_other_project__with_break_inheritance_from_group_level_set_at_project_level(
    configuration_with_break_inheritance_from_group_level_set_at_project_level,
):
    effective_config = configuration_with_break_inheritance_from_group_level_set_at_project_level.get_effective_config_for_project(
        "some_group/my_other_project"
    )

    secret_variables = effective_config["secret_variables"]

    assert secret_variables == {
        "first": {"key": "foo", "value": "bar"},
        "fourth": {"key": "foo4", "value": "bar4"},
    }


def test__get_effective_config_for_my_project__with_break_inheritance_from_common_and_group_level_set_at_group_and_project_level(
    configuration_with_break_inheritance_from_common_and_group_level_set_at_group_and_project_level,
):
    effective_config = configuration_with_break_inheritance_from_common_and_group_level_set_at_group_and_project_level.get_effective_config_for_project(
        "some_group/my_project"
    )

    assert effective_config == {
        "secret_variables": {
            "inherit": False,
            "first": {"key": "foo", "value": "bar"},
            "second": {"key": "bizz", "value": "buzz"},
        },
        "members": {
            "inherit": False,
            "users": {
                "user3": "maintainer",
                "user4": "maintainer",
            },
        },
    }
