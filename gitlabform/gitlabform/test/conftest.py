import pytest

from gitlabform.gitlabform.test import (
    get_gitlab,
    get_group_name,
    create_group,
    get_project_name,
    create_project,
)


@pytest.fixture(scope="session")
def gitlab():
    gl = get_gitlab()
    yield gl  # provide fixture value


@pytest.fixture(scope="class")
def group():
    group_name = get_group_name("")
    create_group(group_name)

    yield group_name

    gl = get_gitlab()
    gl.delete_group(group_name)


@pytest.fixture(scope="class")
def project(group):
    project_name = get_project_name("")
    create_project(group, project_name)

    yield project_name

    gl = get_gitlab()
    gl.delete_project(f"{group}/{project_name}")


@pytest.fixture(scope="class")
def other_project(group):
    project_name = get_project_name("")
    create_project(group, project_name)

    yield project_name

    gl = get_gitlab()
    gl.delete_project(f"{group}/{project_name}")
