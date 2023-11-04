import logging
import textwrap
import time

import gitlab
from gitlab.v4.objects import ProjectHook

from gitlabform import GitLabForm
from gitlabform.gitlab import GitlabWrapper
from gitlabform.gitlab.core import NotFoundException

from tests.acceptance import (
    allowed_codes,
    create_group,
    delete_groups,
    create_project,
)

logger = logging.getLogger(__name__)


test_yaml = """
      config_version: 3
      projects_and_groups:
        "*":
          project_settings:
            visibility: internal
        test_group/mystery:
          project_settings:
            rick: pickle
          hooks:
            "http://plumbus.org/create":
                push_events: true
                merge_requests_events: true
            "http://birdman.chirp/update":
                push_events: true
      """

delete_yaml = """
      config_version: 3
      projects_and_groups:
        "*":
          project_settings:
            visibility: internal
        test_group/mystery:
          project_settings:
            rick: pickle
          hooks:
            "http://plumbus.org/create":
                delete: true
      """

first_hook_dict = {"url": "http://birdman.chirp/update", "push_events": True}

second_hook_dict = {
    "url": "http://plumbus.org/create",
    "push_events": True,
    "merge_requests_events": True,
}


def test_hooks_processor():
    config = textwrap.dedent(test_yaml)
    gf = GitLabForm(
        include_archived_projects=False,
        target="test_group/mystery",
        config_string=config,
    )
    gl = GitlabWrapper(gf.gitlab).get_gitlab()

    with allowed_codes(404):
        gl.groups.delete("test_group")
        # wait for delete to finish
        time.sleep(5)
    group = create_group("test_group")

    project = create_project(group, "mystery")
    bird_hook = project.hooks.create(
        {
            "url": "http://birdman.chirp/update",
            "push_events": False,
            "merge_requests_events": False,
        }
    )

    gf.run()

    project = gl.projects.get("test_group/mystery")
    modified_hooks = project.hooks.list()

    for key, value in first_hook_dict.items():
        assert modified_hooks[0].asdict()[key] == value
    for key, value in second_hook_dict.items():
        assert modified_hooks[1].asdict()[key] == value

    # DELETE ONE PROJECT HOOK
    config = textwrap.dedent(delete_yaml)
    gf = GitLabForm(
        include_archived_projects=False,
        target="test_group/mystery",
        config_string=config,
    )
    gl = GitlabWrapper(gf.gitlab).get_gitlab()
    gf.run()
    project = gl.projects.get("test_group/mystery")
    hooks_after_delete = project.hooks.list()

    assert len(hooks_after_delete) == len(modified_hooks) - 1
    assert modified_hooks[1] not in hooks_after_delete

    # clean up
    with allowed_codes(404):
        gl.groups.delete("test_group")
    time.sleep(5)
    return None
