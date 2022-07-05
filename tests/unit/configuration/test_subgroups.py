import logging
import pytest

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_subgroups_and_projects():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          setting_from_group: foo

      some_group/subgroup_level_1/*:
        project_settings:
          setting_from_subgroup_level_1: foo

      some_group/subgroup_level_1/some_project:
        project_settings:
          setting_from_project: foo

      some_group/subgroup_level_1/subgroup_level_2/*:
        project_settings:
          setting_from_subgroup_level_2: foo

      some_group/subgroup_level_1/subgroup_level_2/some_project:
          project_settings:
            setting_from_project: foo
    """
    return Configuration(config_string=config_yaml)


def test__get_effective_config_for_project__level1(
    configuration_with_subgroups_and_projects,
):
    effective_config = (
        configuration_with_subgroups_and_projects.get_effective_config_for_project(
            "some_group/subgroup_level_1/some_project"
        )
    )

    additive__project_settings = effective_config["project_settings"]

    # for project settings all the levels up are inherited
    assert additive__project_settings == {
        "setting_from_group": "foo",
        "setting_from_subgroup_level_1": "foo",
        "setting_from_project": "foo",
    }


def test__get_effective_config_for_project__level2(
    configuration_with_subgroups_and_projects,
):
    effective_config = (
        configuration_with_subgroups_and_projects.get_effective_config_for_project(
            "some_group/subgroup_level_1/subgroup_level_2/some_project"
        )
    )

    additive__project_settings = effective_config["project_settings"]

    # the settings should be inherited from all levels
    assert additive__project_settings == {
        "setting_from_group": "foo",
        "setting_from_subgroup_level_1": "foo",
        "setting_from_subgroup_level_2": "foo",
        "setting_from_project": "foo",
    }


@pytest.fixture
def configuration_with_subgroups_only():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        group_members:
          my-user:
            access_level: 10

      some_group/subgroup/*:
        group_members:
          my-user2:
            access_level: 20
            
      some_group/subgroup/subsubgroup/*:
        group_members:
          my-user3:
            access_level: 30
    """
    return Configuration(config_string=config_yaml)


def test__get_effective_subgroup_config__level1(configuration_with_subgroups_only):
    effective_config = configuration_with_subgroups_only.get_effective_subgroup_config(
        "some_group/subgroup"
    )

    # the settings should be inherited from all levels
    assert effective_config == {
        "group_members": {
            "my-user": {"access_level": 10},
            "my-user2": {
                "access_level": 20,
            },
        },
    }


def test__get_effective_subgroup_config__level2(configuration_with_subgroups_only):
    effective_config = configuration_with_subgroups_only.get_effective_subgroup_config(
        "some_group/subgroup/subsubgroup"
    )

    # the settings should be inherited from all levels
    assert effective_config == {
        "group_members": {
            "my-user": {"access_level": 10},
            "my-user2": {
                "access_level": 20,
            },
            "my-user3": {
                "access_level": 30,
            },
        },
    }
