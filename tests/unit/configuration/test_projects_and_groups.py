import logging
import pytest

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_with_only_group_and_project():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: bar
        hooks:
          a:
            foo: bar

      some_group/some_project:
        project_settings:
          bar: foo
        hooks:
          b:
            bar: foo
    """

    return Configuration(config_string=config_yaml)


def test__get_effective_config_for_project__other_project(
    configuration_with_only_group_and_project,
):
    effective_config = (
        configuration_with_only_group_and_project.get_effective_config_for_project(
            "project_not_in_config/group_not_in_config"
        )
    )

    assert effective_config == {}


def test__get_effective_config_for_project__project_from_config__additive_project_settings(
    configuration_with_only_group_and_project,
):
    effective_config = (
        configuration_with_only_group_and_project.get_effective_config_for_project(
            "some_group/some_project"
        )
    )

    additive__project_settings = effective_config["project_settings"]

    # merged hashes from group and project levels
    assert additive__project_settings == {"foo": "bar", "bar": "foo"}


def test__get_effective_config_for_project__project_from_config__additive_hooks(
    configuration_with_only_group_and_project,
):
    effective_config = (
        configuration_with_only_group_and_project.get_effective_config_for_project(
            "some_group/some_project"
        )
    )

    additive__hooks = effective_config["hooks"]
    assert additive__hooks == {
        "a": {"foo": "bar"},
        "b": {"bar": "foo"},
    }  # added from both group and project level


def test__get_effective_config_for_project__with_multiple_levels():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        merge_requests:
          approvals:
            approvals_before_merge: 3
          approvers:
            - common_approvers

      "some_group/*":
        merge_requests:
          approvals:
            reset_approvals_on_push: true
          approvers:
            - group_approvers

      "some_group/my_project":
        merge_requests:
          approvals:
            reset_approvals_on_push: false
            disable_overriding_approvers_per_merge_request: true
          approvers:
            - project_approvers
    """

    effective_config = Configuration(
        config_string=config_yaml
    ).get_effective_config_for_project("some_group/my_project")

    assert effective_config == {
        "merge_requests": {
            "approvals": {
                # dict is merged - below is the config from common + group + project level
                "approvals_before_merge": 3,
                "reset_approvals_on_push": False,
                "disable_overriding_approvers_per_merge_request": True,
            },
            "approvers": [
                # list is overriden - only the element from the project level config is here
                "project_approvers",
            ],
        }
    }


def test__get_effective_config_for_project__configuration_for_other_project():
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
          second:
            key: foo
            value: bar
    """

    effective_config = Configuration(
        config_string=config_yaml
    ).get_effective_config_for_project("some_group/some_project_after_defined")

    assert effective_config == {
        "secret_variables": {
            "first": {
                "key": "foo",
                "value": "bar",
            },
        }
    }
