import logging

import pytest

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


@pytest.fixture
def configuration_for_skip_groups_skip_projects():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        group_settings:
          one: two
        project_settings:
          three: four

    skip_groups:
    - group-skip
    - group-skip-wildcard/*
    - group-not-skip/subgroup-skip
    - group-not-skip/subgroup-skip-wildcard/*

    skip_projects:
    - project-skip
    - group-skip/project-skip
    - group-skip-wildcard/*
    - group-not-skip/project-skip
    - group-not-skip/subgroup-skip-wildcard/*

    """

    return Configuration(config_string=config_yaml)


@pytest.mark.parametrize(
    "project,is_skipped",
    [
        ("project-skip", True),
        ("project-not-skip", False),
        ("group-not-skip/project-not-skip", False),
        ("group-skip/project-not-skip", False),
        ("group-skip-wildcard/project-skip", True),
        ("group-skip-wildcard/subgroup-a/project-skip", True),
        ("group-skip-wildcard/subgroup-a/subgroup-b/project-skip", True),
        ("group-not-skip/subgroup-not-skip/project-not-skip", False),
        ("group-not-skip/subgroup-skip-wildcard/project-skip", True),
        ("group-not-skip/subgroup-not-skip/project-not-skip", False),
        ("group-not-skip/subgroup-skip/project-not-skip", False),
    ],
)
def test__config_skip_project(project, is_skipped, request):

    configuration_for_skip_groups_skip_projects = request.getfixturevalue(
        "configuration_for_skip_groups_skip_projects"
    )

    assert (
        configuration_for_skip_groups_skip_projects.is_project_skipped(project)
        == is_skipped
    )


@pytest.mark.parametrize(
    "group,is_skipped",
    [
        ("group-not-skip", False),
        ("group-skip", True),
        ("group-skip-wildcard", True),
        ("group-skip-wildcard/subgroup-a", True),
        ("group-skip-wildcard/subgroup-a/subgroup-b", True),
        ("group-not-skip/subgroup-not-skip", False),
        ("group-not-skip/subgroup-skip-wildcard", True),
        ("group-not-skip/subgroup-skip-wildcard/subgroup-skip", True),
        ("group-not-skip/subgroup-not-skip", False),
    ],
)
def test__config_skip_group(group, is_skipped, request):

    configuration_for_skip_groups_skip_projects = request.getfixturevalue(
        "configuration_for_skip_groups_skip_projects"
    )

    assert (
        configuration_for_skip_groups_skip_projects.is_group_skipped(group)
        == is_skipped
    )
