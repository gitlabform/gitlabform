import logging
import pytest

from gitlabform.configuration import Configuration
from gitlabform import EXIT_INVALID_INPUT

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_inheritance_break_from_subgroups_set_at_project_level():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: bar
        hooks:
          a:
            foo: bar

      some_group/subgroup_level_1/*:
        project_settings:
          foo: bar2
        hooks:
          a:
            foo: bar2

      some_group/subgroup_level_1/subgroup_level_2/*:
        project_settings:
          foo: bar3
        hooks:
          a:
            foo: bar3

      some_group/some_project:
        project_settings:
          bar: something_else
        hooks:
          b:
            bar: something_else

      some_group/subgroup_level_1/some_project:
          project_settings:
            inherit: false
            bar: something_else2
          hooks:
            b:
              bar: something_else2

      some_group/subgroup_level_1/subgroup_level_2/some_project:
          project_settings:
            inherit: false
            bar: something_else3
          hooks:
            b:
              bar: something_else3
    """
    return Configuration(config_string=config_yaml)


def test__get_effective_config_for_group__with_invalid_inheritance_break_set_at_group_level():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        group_members:
          inherit: false
          my-user:
            access_level: 10
        enforce_group_members: true
    """

    with pytest.raises(SystemExit) as exception:
        Configuration(config_string=config_yaml).get_effective_config_for_group(
            "some_group"
        )
    assert exception.type == SystemExit
    assert exception.value.code == EXIT_INVALID_INPUT


def test__get_effective_config_for_group__with_invalid_inheritance_break_set_at_subgroup_level():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/subgroup/*:
        group_members:
          inherit: false
          my-user:
            access_level: 10
        enforce_group_members: true
    """

    with pytest.raises(SystemExit) as exception:
        Configuration(config_string=config_yaml).get_effective_config_for_group(
            "some_group/subgroup"
        )
    assert exception.type == SystemExit
    assert exception.value.code == EXIT_INVALID_INPUT


def test__get_effective_config_for_subgroup__with_break_inheritance_from_group_level_set_at_subgroup_level():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        group_members:
          my-user:
            access_level: developer
        enforce_group_members: true

      some_group/subgroup/*:
        group_members:
          inherit: false
          my-user2:
            access_level: maintainer
        enforce_group_members: true
    """

    configuration = Configuration(config_string=config_yaml)

    effective_config = configuration.get_effective_subgroup_config(
        "some_group/subgroup"
    )

    assert effective_config == {
        "group_members": {
            "my-user2": {
                "access_level": "maintainer",
            },
        },
        "enforce_group_members": True,
    }


def test__get_effective_config_for_level_1_project__with_inheritance_break_from_subgroups_set_at_project_level(
    configuration_with_inheritance_break_from_subgroups_set_at_project_level,
):
    effective_config = configuration_with_inheritance_break_from_subgroups_set_at_project_level.get_effective_config_for_project(
        "some_group/subgroup_level_1/some_project"
    )

    # project and only subgroup level 1
    assert effective_config == {
        "project_settings": {
            "bar": "something_else2",
        },
        "hooks": {"a": {"foo": "bar2"}, "b": {"bar": "something_else2"}},
    }


def test__get_effective_config_for_level_2_project__with_inheritance_break_from_subgroups_set_at_project_level(
    configuration_with_inheritance_break_from_subgroups_set_at_project_level,
):
    effective_config = configuration_with_inheritance_break_from_subgroups_set_at_project_level.get_effective_config_for_project(
        "some_group/subgroup_level_1/subgroup_level_2/some_project"
    )

    # project and only subgroup level 2
    assert effective_config == {
        "project_settings": {
            "bar": "something_else3",
        },
        "hooks": {"a": {"foo": "bar3"}, "b": {"bar": "something_else3"}},
    }
