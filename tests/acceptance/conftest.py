import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    get_gitlab,
    create_group,
    create_groups,
    delete_groups,
    create_project,
    get_random_name,
    create_users,
    delete_users,
)


@pytest.fixture(scope="session")
def gitlab():
    gl = get_gitlab()
    yield gl  # provide fixture value


@pytest.fixture(scope="class")
def group_and_project(group, project):
    return f"{group}/{project}"


@pytest.fixture(scope="function")
def group_and_project_for_function(group, project_for_function):
    return f"{group}/{project_for_function}"


@pytest.fixture(scope="class")
def group():
    group_name = get_random_name("group")
    create_group(group_name)

    yield group_name

    gl = get_gitlab()
    gl.delete_group(group_name)


@pytest.fixture(scope="function")
def group_for_function():
    group_name = get_random_name("group")
    create_group(group_name)

    yield group_name

    gl = get_gitlab()
    gl.delete_group(group_name)


@pytest.fixture(scope="class")
def other_group():
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    group_name = get_random_name("group")
    create_group(group_name)

    yield group_name

    gl = get_gitlab()
    gl.delete_group(group_name)


@pytest.fixture(scope="class")
def sub_group(group):
    gl = get_gitlab()
    parent_id = gl.get_group_id_case_insensitive(group)
    group_name = get_random_name("subgroup")
    create_group(group_name, parent_id)

    yield group + "/" + group_name

    gl = get_gitlab()
    gl.delete_group(group + "/" + group_name)


@pytest.fixture(scope="class")
def project(group):
    project_name = get_random_name("project")
    create_project(group, project_name)

    yield project_name

    gl = get_gitlab()
    gl.delete_project(f"{group}/{project_name}")


@pytest.fixture(scope="function")
def project_for_function(group):
    project_name = get_random_name("project")
    create_project(group, project_name)

    yield project_name

    gl = get_gitlab()
    gl.delete_project(f"{group}/{project_name}")


@pytest.fixture(scope="class")
def other_project(group):
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    project_name = get_random_name("project")
    create_project(group, project_name)

    yield project_name

    gl = get_gitlab()
    gl.delete_project(f"{group}/{project_name}")


@pytest.fixture(scope="class")
def groups(users):
    no_of_groups = 4

    group_name_base = get_random_name("group")
    groups = create_groups(group_name_base, no_of_groups)

    yield groups

    delete_groups(group_name_base, no_of_groups)


@pytest.fixture(scope="class")
def users(group):
    no_of_users = 4

    username_base = get_random_name("user")
    users = create_users(username_base, no_of_users)

    yield users

    delete_users(username_base, no_of_users)


@pytest.fixture(scope="class")
def other_users():
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    no_of_users = 4

    username_base = get_random_name("user")
    users = create_users(username_base, no_of_users)

    yield users

    delete_users(username_base, no_of_users)


@pytest.fixture(scope="class")
def branch(gitlab, group_and_project):
    name = get_random_name("branch")
    gitlab.create_branch(group_and_project, name, "main")

    yield name

    gitlab.delete_branch(group_and_project, name)


@pytest.fixture(scope="class")
def other_branch(gitlab, group_and_project):
    # TOOD: deduplicate
    name = get_random_name("other_branch")
    gitlab.create_branch(group_and_project, name, "main")

    yield name

    gitlab.delete_branch(group_and_project, name)


class User:
    def __init__(self, name, id):
        self.name = name
        self.id = id


@pytest.fixture(scope="class")
def make_user(gitlab, group_and_project):
    username_base = get_random_name("user")
    created_users = []

    def _make_user(level=AccessLevel.DEVELOPER, add_to_project=True):
        last_id = len(created_users) + 1
        username = f"{username_base}_{last_id}"
        user = gitlab.create_user(
            username + "@example.com", username + " Example", username, "password"
        )
        user_obj = User(username, user["id"])
        if add_to_project:
            gitlab.add_member_to_project(
                group_and_project, None, level.value, user_id=user["id"]
            )
        created_users.append(user_obj)
        return user_obj

    yield _make_user

    for user in created_users:
        gitlab.delete_user(None, user_id=user.id)


@pytest.fixture(scope="class")
def three_members(gitlab, group_and_project, make_user):
    member1 = make_user()
    member2 = make_user()
    member3 = make_user()

    yield [member1.name, member2.name, member3.name]


@pytest.fixture(scope="function")
def outsider_user(gitlab, group_and_project):
    username = get_random_name("outsider_user")
    user = gitlab.create_user(
        username + "@example.com", username + " Example", username, "password"
    )
    user_obj = User(username, user["id"])

    yield user_obj.name

    gitlab.delete_user(None, user_id=user_obj.id)
