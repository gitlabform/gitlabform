from datetime import date, timedelta
import os
from typing import Callable, Optional, Generator, List

import pytest
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from gitlab import Gitlab
from gitlab.v4.objects import Group, Project, User, ProjectAccessToken, GroupAccessToken

from gitlabform.gitlab import AccessLevel, GitLab
from tests.acceptance import (
    allowed_codes,
    create_group,
    create_groups,
    delete_groups,
    create_project,
    get_random_name,
    create_users,
    get_random_password,
)


@pytest.fixture(scope="session")
def gl():
    return Gitlab(os.getenv("GITLAB_URL"), private_token=os.getenv("GITLAB_TOKEN"))


@pytest.fixture(autouse=True)
def requires_license(gl: Gitlab, request):
    if not request.node.get_closest_marker("requires_license"):
        return

    gitlab_license = gl.get_license()
    if not gitlab_license or gitlab_license["expired"]:
        pytest.skip("this test requires a GitLab license (Paid/Trial)")


@pytest.fixture(scope="session")
def root_user(gl):
    return gl.users.list(username="root")[0]


@pytest.fixture(scope="class")
def group(gl: Gitlab) -> Generator[Optional[Group], None, None]:
    group_name = get_random_name("group")
    gitlab_group = create_group(group_name)

    yield gitlab_group

    with allowed_codes(404):
        gl.groups.delete(group_name)


@pytest.fixture(scope="function")
def group_for_function(gl: Gitlab):
    group_name = get_random_name("group")
    gitlab_group = create_group(group_name)

    yield gitlab_group

    with allowed_codes(404):
        gl.groups.delete(group_name)


@pytest.fixture(scope="class")
def other_group(gl: Gitlab):
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    group_name = get_random_name("group")
    group = create_group(group_name)

    yield group

    with allowed_codes(404):
        gl.groups.delete(group_name)


@pytest.fixture(scope="class")
def third_group(gl: Gitlab):
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    group_name = get_random_name("group")
    group = create_group(group_name)

    yield group

    with allowed_codes(404):
        gl.groups.delete(group_name)


@pytest.fixture(scope="class")
def subgroup(gl: Gitlab, group: Group):
    subgroup_name = get_random_name("subgroup")
    gitlab_subgroup = create_group(subgroup_name, group.id)

    yield gitlab_subgroup

    with allowed_codes(404):
        gl.groups.delete(f"{group.full_path}/{subgroup_name}")


@pytest.fixture(scope="class")
def other_subgroup(gl: Gitlab, group: Group):
    subgroup_name = get_random_name("subgroup")
    gitlab_subgroup = create_group(subgroup_name, group.id)

    yield gitlab_subgroup

    with allowed_codes(404):
        gl.groups.delete(f"{group.full_path}/{subgroup_name}")


@pytest.fixture(scope="class")
def project(gl: Gitlab, group: Group):
    project_name = get_random_name("project")
    gitlab_project = create_project(group, project_name)

    yield gitlab_project

    gitlab_project.delete()


@pytest.fixture(scope="class")
def project_in_subgroup(gl: Gitlab, subgroup: Group):
    project_name = get_random_name("project")
    gitlab_project = create_project(subgroup, project_name)

    yield gitlab_project

    gitlab_project.delete()


@pytest.fixture(scope="class")
def project_in_other_subgroup(gl: Gitlab, other_subgroup: Group):
    project_name = get_random_name("project")
    gitlab_project = create_project(other_subgroup, project_name)

    yield gitlab_project

    gitlab_project.delete()


@pytest.fixture(scope="function")
def project_for_function(gl: Gitlab, group: Group):
    project_name = get_random_name("project")
    gitlab_project = create_project(group, project_name)

    yield gitlab_project

    gitlab_project.delete()


@pytest.fixture(scope="class")
def other_project(gl: Gitlab, group):
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    project_name = get_random_name("project")
    gitlab_project = create_project(group, project_name)

    yield gitlab_project

    gitlab_project.delete()


@pytest.fixture(scope="class")
def groups(users):
    no_of_groups = 4

    group_name_base = get_random_name("group")
    groups = create_groups(group_name_base, no_of_groups)

    yield groups

    delete_groups(group_name_base, no_of_groups)


@pytest.fixture(scope="class")
def group_to_invite_to_project(
    gl: Gitlab,
) -> Generator[Callable[[Project, AccessLevel], Group], None, None]:
    group_name_base = get_random_name("group")
    created_groups: List[Group] = []

    def _group_to_invite_to_project(
        project: Project, access_level: AccessLevel = AccessLevel.DEVELOPER
    ) -> Group:
        group_index = len(created_groups) + 1
        group_name = f"{group_name_base}_{group_index}"
        gitlab_group = create_group(group_name)

        project.share(gitlab_group.id, access_level)
        created_groups.append(gitlab_group)

        return gitlab_group

    yield _group_to_invite_to_project

    for group in created_groups:
        with allowed_codes(404):
            gl.groups.delete(group.id)


@pytest.fixture(scope="class")
def users(group):
    no_of_users = 4

    username_base = get_random_name("user")
    users = create_users(username_base, no_of_users)

    yield users

    for user in users:
        user.delete()


@pytest.fixture(scope="class")
def other_users():
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    no_of_users = 4

    username_base = get_random_name("user")
    users = create_users(username_base, no_of_users)

    yield users

    for user in users:
        user.delete()


@pytest.fixture(scope="class")
def branch(project):
    name = get_random_name("branch")
    branch = project.branches.create({"branch": name, "ref": "main"})

    yield name

    branch.delete()


@pytest.fixture(scope="class")
def other_branch(project):
    # TODO: deduplicate
    name = get_random_name("other_branch")
    branch = project.branches.create({"branch": name, "ref": "main"})

    yield name

    branch.delete()


@pytest.fixture(scope="class")
def tag(project):
    name = get_random_name("tag")
    tag = project.tags.create({"tag_name": name, "ref": "main"})

    yield name

    # Normally the tag deletion would be here for post-test cleanup.
    # But protected tags can't be deleted. It has to be unprotect first
    # and then delete. Since the containing project gets deleted anyways,
    # it should be fine if the tag deletion doesn't happen from this fixture.
    #
    # tag.delete()


@pytest.fixture(scope="class")
def make_user(
    gl, project
) -> Generator[Callable[[AccessLevel, bool], User], None, None]:
    username_base = get_random_name("user")
    created_users: List[User] = []

    def _make_user(
        level: AccessLevel = AccessLevel.DEVELOPER, add_to_project: bool = True
    ) -> User:
        last_id = len(created_users) + 1
        username = f"{username_base}_{last_id}"
        user = gl.users.create(
            {
                "username": username,
                "email": username + "@example.com",
                "name": username + " Example",
                "password": get_random_password(),
            }
        )
        if add_to_project:
            project.members.create({"user_id": user.id, "access_level": level.value})
        created_users.append(user)
        return user

    yield _make_user

    for user in created_users:
        with allowed_codes(404):
            gl.users.delete(user.id)


@pytest.fixture(scope="class")
def make_project_access_token(
    project,
) -> Generator[
    Callable[[Project, AccessLevel, List[str]], ProjectAccessToken], None, None
]:
    token_name_base = get_random_name("user")
    created_tokens: List[ProjectAccessToken] = []

    def _make_project_access_token(
        target_project=project,
        level: AccessLevel = AccessLevel.DEVELOPER,
        scopes: List[str] = ["api"],
    ) -> ProjectAccessToken:
        last_id = len(created_tokens) + 1
        token_name = f"{token_name_base}_{last_id}_bot"
        expires_at = (date.today() + timedelta(days=30)).isoformat()
        token = target_project.access_tokens.create(
            {
                "access_level": level,
                "name": token_name,
                "scopes": scopes,
                "expires_at": expires_at,
            }
        )
        created_tokens.append(token)
        return token

    yield _make_project_access_token

    for token in created_tokens:
        with allowed_codes(404):
            project.access_tokens.delete(token.id)


@pytest.fixture(scope="class")
def make_group_access_token(
    group,
) -> Generator[Callable[[AccessLevel, List[str]], GroupAccessToken], None, None]:
    token_name_base = get_random_name("user")
    created_tokens: List[GroupAccessToken] = []

    def _make_group_access_token(
        level: AccessLevel = AccessLevel.DEVELOPER, scopes: List[str] = ["api"]
    ) -> GroupAccessToken:
        last_id = len(created_tokens) + 1
        token_name = f"{token_name_base}_{last_id}_bot"
        expires_at = (date.today() + timedelta(days=30)).isoformat()
        token = group.access_tokens.create(
            {
                "access_level": level,
                "name": token_name,
                "scopes": scopes,
                "expires_at": expires_at,
            }
        )
        created_tokens.append(token)
        return token

    yield _make_group_access_token

    for token in created_tokens:
        with allowed_codes(404):
            group.access_tokens.delete(token.id)


@pytest.fixture(scope="class")
def three_members(make_user):
    member1 = make_user()
    member2 = make_user()
    member3 = make_user()

    yield [member1.name, member2.name, member3.name]


@pytest.fixture(scope="function")
def outsider_user(gl):
    username = get_random_name("outsider_user")
    user = gl.users.create(
        {
            "username": username,
            "email": username + "@example.com",
            "name": username + " Example",
            "password": get_random_password(),
        }
    )

    yield user

    gl.users.delete(user.id)


@pytest.fixture(scope="function")
def public_ssh_key():
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )

    yield public_key.decode("UTF-8")


@pytest.fixture(scope="function")
def other_public_ssh_key():
    # TODO: deduplicate this - it's a copy and paste from the above fixture
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
    )

    yield public_key.decode("UTF-8")


@pytest.fixture(scope="class")
def token_from_env_var():
    token = os.environ["GITLAB_TOKEN"]
    del os.environ["GITLAB_TOKEN"]

    yield token

    os.environ["GITLAB_TOKEN"] = token
