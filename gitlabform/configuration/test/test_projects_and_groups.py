import logging
import pytest
from gitlabform.configuration import ConfigurationProjectsAndGroups


logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_only_group_and_project():
    config_yaml = """
---
group_settings:
  some_group:
    project_settings:
      foo: bar
    hooks:
      a:
        foo: bar

project_settings:
  some_group/some_project:
    project_settings:
      bar: foo
    hooks:
      b:
        bar: foo
"""

    return ConfigurationProjectsAndGroups(config_string=config_yaml)


@pytest.fixture
def configuration_with_subgroups():
    config_yaml = """
---
group_settings:
  some_group:
    project_settings:
      foo: bar
    hooks:
      a:
        foo: bar

  some_group/subgroup_level_1:
    project_settings:
      foo: bar2
    hooks:
      a:
        foo: bar2

  some_group/subgroup_level_1/subgroup_level_2:
    project_settings:
      foo: bar3
    hooks:
      a:
        foo: bar3

project_settings:
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

    return ConfigurationProjectsAndGroups(config_string=config_yaml)


@pytest.fixture
def configuration_with_common_and_group():
    config_yaml = """
---
common_settings:
  merge_requests:
    approvals:
      approvals_before_merge: 3

group_settings:
  "group_name":
    merge_requests:
      approvals:
        merge_requests_author_approval: true
"""

    return ConfigurationProjectsAndGroups(config_string=config_yaml)


def test__get_effective_config_for_project__other_project(
    configuration_with_only_group_and_project,
):

    x = configuration_with_only_group_and_project.get_effective_config_for_project(
        "project_not_in_config/group_not_in_config"
    )

    assert x == {}


def test__get_effective_config_for_project__project_from_config__additive_project_settings(
    configuration_with_only_group_and_project,
):

    x = configuration_with_only_group_and_project.get_effective_config_for_project(
        "some_group/some_project"
    )

    additive__project_settings = x["project_settings"]

    # merged hashes from group and project levels
    assert additive__project_settings == {"foo": "bar", "bar": "foo"}


def test__get_effective_config_for_project__project_from_config__additive_hooks(
    configuration_with_only_group_and_project,
):

    x = configuration_with_only_group_and_project.get_effective_config_for_project(
        "some_group/some_project"
    )

    additive__hooks = x["hooks"]
    assert additive__hooks == {
        "a": {"foo": "bar"},
        "b": {"bar": "foo"},
    }  # added from both group and project level


def test__get_effective_config_for_project__project_from_config__level1(
    configuration_with_subgroups,
):

    x = configuration_with_subgroups.get_effective_config_for_project(
        "some_group/subgroup_level_1/some_project"
    )

    additive__project_settings = x["project_settings"]

    # project and only subgroup level 1
    assert additive__project_settings == {"foo": "bar2", "bar": "something_else2"}


def test__get_effective_config_for_project__project_from_config__level2(
    configuration_with_subgroups,
):

    x = configuration_with_subgroups.get_effective_config_for_project(
        "some_group/subgroup_level_1/subgroup_level_2/some_project"
    )

    additive__project_settings = x["project_settings"]

    # project and only subgroup level 2
    assert additive__project_settings == {"foo": "bar3", "bar": "something_else3"}


def test__get_effective_config_for_common_and_group(
    configuration_with_common_and_group,
):

    x = configuration_with_common_and_group.get_effective_config_for_project(
        "group_name/project_name"
    )

    assert "approvals" in x["merge_requests"]

    assert "approvals_before_merge" in x["merge_requests"]["approvals"]
    assert x["merge_requests"]["approvals"]["approvals_before_merge"] == 3

    assert "merge_requests_author_approval" in x["merge_requests"]["approvals"]
    assert x["merge_requests"]["approvals"]["merge_requests_author_approval"] is True
