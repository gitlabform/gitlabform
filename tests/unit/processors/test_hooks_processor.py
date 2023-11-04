import logging
from logging import debug
import os
import textwrap
import time
import pytest
from typing import TYPE_CHECKING

import gitlab
from gitlab.v4.objects import Hook, Group, Project

from gitlabform import GitLabForm
from gitlabform.gitlab import GitlabWrapper

import tests.acceptance as acc

logger = logging.getLogger(__name__)

conf_path = "/home/godot/Projects/OpenSource/gitlabform/config.yml"

# class TestHooksProcessor:

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


def test_create_update():
    config = textwrap.dedent(test_yaml)
    gf = GitLabForm(
        include_archived_projects=False,
        target="test_group/mystery",
        config_string=config,
    )
    gl = GitlabWrapper(gf.gitlab).get_gitlab()
    # clean-up in case this runs on a gitlab instance that has the group already
    try:
        group = gl.groups.get("test_group")
        gl.groups.delete("test_group")
        # wait for delete to finish
        time.sleep(5)
    except Exception:
        pass
    # set-up the config to modify
    group = gl.groups.create(
        {"name": "test_group", "path": "test_group", "visibility": "internal"}
    )

    project = gl.projects.create(
        {
            "name": "mystery",
            "path": "mystery",
            "namespace_id": group.id,
            "default_branch": "main",
        }
    )

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
    if TYPE_CHECKING:
        for h in modified_hooks:
            assert isinstance(h, ProjectHook)

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

    return hooks_after_delete
