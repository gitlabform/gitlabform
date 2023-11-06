import logging
import time
from typing import TYPE_CHECKING

import gitlab
from gitlab.v4.objects import ProjectHook, Project, Group

from tests.acceptance import allowed_codes, run_gitlabform, create_group, create_project

logger = logging.getLogger(__name__)


def create_test_hook(project: Project):
    hook = project.hooks.create(
        {
            "url": "http://birdman.chirp/update",
            "push_events": False,
            "merge_requests_events": False,
        }
    )
    if TYPE_CHECKING:
        assert isinstance(hook, ProjectHook)
    return hook


def prepare_project(gl, group: str, project: str):
    with allowed_codes(404):
        gl.groups.delete(group)
        # wait for delete to finish
        time.sleep(6)
    created_group: Group = create_group(group)
    created_project: Project = create_project(created_group, project)
    return


def reset_gitlab(gl):
    with allowed_codes(404):
        gl.groups.delete("test_group")
        time.sleep(5)
    return

test_yaml = """
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

birdman_dict = {"url": "http://birdman.chirp/update", "push_events": True}

plumbus_dict = {
        "url": "http://plumbus.org/create",
        "push_events": True,
        "merge_requests_events": True,
    }


def test_project_hooks_create(gl):
    prepare_project(gl, "test_group", "mystery")
    target = "test_group/mystery"
    run_gitlabform(test_yaml, target, include_archived_projects=False)

    project = gl.projects.get("test_group/mystery")
    modified_hooks = project.hooks.list()

    assert len(modified_hooks) == 2
    for key, value in birdman_dict.items():
        assert modified_hooks[0].asdict()[key] == value
    for key, value in plumbus_dict.items():
        assert modified_hooks[1].asdict()[key] == value

    reset_gitlab(gl)


def test_project_hooks_update(gl):
    prepare_project(gl, "test_group", "mystery")
    target = "test_group/mystery"
    project = gl.projects.get("test_group/mystery")
    hook: ProjectHook = create_test_hook(project)

    run_gitlabform(test_yaml, target, include_archived_projects=False)

    project = gl.projects.get("test_group/mystery")
    modified_hook = next(
        p for p in project.hooks.list() if p.url == "http://birdman.chirp/update"
    )
    for key, value in birdman_dict.items():
        assert modified_hook.asdict()[key] == value

    reset_gitlab(gl)


def test_project_hook_delete(gl):
    prepare_project(gl, "test_group", "mystery")
    target = "test_group/mystery"
    run_gitlabform(test_yaml, target, include_archived_projects=False)
    project = gl.projects.get("test_group/mystery")
    hooks_before = project.hooks.list()

    run_gitlabform(delete_yaml, target, include_archived_projects=False)

    project_after = gl.projects.get("test_group/mystery")
    hooks_after = project_after.hooks.list()

    assert len(hooks_after) == len(hooks_before) - 1
    assert hooks_before[1] not in hooks_after
    assert len([h for h in hooks_after if h.url == "http://plumbus.org/create"]) == 0

    reset_gitlab(gl)
