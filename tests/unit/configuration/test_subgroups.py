import logging

import pytest
from gitlabform.configuration import Configuration

from gitlabform.configuration.projects_and_groups import ConfigurationProjectsAndGroups

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_subgroups_and_projects():
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
            bar: something_else2
          hooks:
            b:
              bar: something_else2

      some_group/subgroup_level_1/subgroup_level_2/some_project:
          project_settings:
            bar: something_else3
          hooks:
            b:
              bar: something_else3
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def configuration_with_subgroups():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        group_members:
          my-user:
            access_level: 10
        enforce_group_members: true

      some_group/subgroup/*:
        group_members:
          my-user2:
            access_level: 20
        enforce_group_members: true
    """
    return Configuration(config_string=config_yaml)


def test__get_effective_config_for_project__project_from_config__level1(
    configuration_with_subgroups_and_projects,
):
    effective_config = (
        configuration_with_subgroups_and_projects.get_effective_config_for_project(
            "some_group/subgroup_level_1/some_project"
        )
    )

    additive__project_settings = effective_config["project_settings"]

    # project and only subgroup level 1
    assert additive__project_settings == {"foo": "bar2", "bar": "something_else2"}


def test__get_effective_config_for_project__project_from_config__level2(
    configuration_with_subgroups_and_projects,
):
    effective_config = (
        configuration_with_subgroups_and_projects.get_effective_config_for_project(
            "some_group/subgroup_level_1/subgroup_level_2/some_project"
        )
    )

    additive__project_settings = effective_config["project_settings"]

    # project and only subgroup level 2
    assert additive__project_settings == {"foo": "bar3", "bar": "something_else3"}


def test__get_effective_config_for_subgroup(
    configuration_with_subgroups,
):
    effective_config = configuration_with_subgroups.get_effective_config_for_group(
        "some_group/subgroup"
    )

    assert effective_config == {
        "group_members": {
            "my-user2": {
                "access_level": 20,
            },
        },
        "enforce_group_members": True,
    }
