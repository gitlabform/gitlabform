from unittest.mock import MagicMock

import pytest

from gitlabform import GitLabForm
from gitlabform.configuration import Configuration
from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.lists import Groups, Projects

APPLICATION_ONLY_CONFIG = """
application:
  settings:
    require_two_factor_authentication: true
"""

PROJECTS_AND_GROUPS_CONFIG = """
projects_and_groups:
  group/project:
    project_settings:
      visibility: internal
"""


def make_gitlabform(config_yaml: str) -> GitLabForm:
    """
    Creates a GitLabForm instance without running its constructor, which needs a GitLab connection,
    with no groups and no projects returned by the providers.
    """
    gf = GitLabForm.__new__(GitLabForm)
    gf.noop = False
    gf.configuration = Configuration(config_string=config_yaml)
    gf.groups_provider = MagicMock()
    gf.groups_provider.get_groups.return_value = Groups()
    gf.projects_provider = MagicMock()
    gf.projects_provider.get_projects.return_value = Projects()
    gf.groups_and_projects_filters = MagicMock()
    return gf


def test__no_groups_and_projects_with_application_only_config():
    gf = make_gitlabform(APPLICATION_ONLY_CONFIG)

    projects, groups = gf._get_groups_and_projects("ALL_DEFINED")

    assert projects == []
    assert groups == []


@pytest.mark.parametrize("target", ["ALL", "ALL_DEFINED", "group/project"])
def test__no_groups_and_projects_without_application_config(target):
    gf = make_gitlabform(PROJECTS_AND_GROUPS_CONFIG)

    with pytest.raises(SystemExit) as e:
        gf._get_groups_and_projects(target)
    assert e.value.code == EXIT_INVALID_INPUT


@pytest.mark.parametrize("target", ["ALL", "group/project"])
def test__no_groups_and_projects_with_application_only_config_and_other_targets(target):
    gf = make_gitlabform(APPLICATION_ONLY_CONFIG)

    with pytest.raises(SystemExit) as e:
        gf._get_groups_and_projects(target)
    assert e.value.code == EXIT_INVALID_INPUT
