import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    allowed_codes,
    create_group,
    create_project,
    get_random_name,
    run_gitlabform,
)


@pytest.fixture(scope="function")
def root_and_subgroup_projects(group_for_function, subgroup_for_function):
    root_project = create_project(group_for_function, get_random_name("project"))
    subgroup_project = create_project(subgroup_for_function, get_random_name("project"))

    yield root_project, subgroup_project

    with allowed_codes(404):
        subgroup_project.delete()

    with allowed_codes(404):
        root_project.delete()


@pytest.fixture(scope="function")
def nested_subgroup_for_function(gl, group_for_function, subgroup_for_function):
    subsubgroup_name = get_random_name("subgroup")
    gitlab_subsubgroup = create_group(subsubgroup_name, subgroup_for_function.id)

    yield gitlab_subsubgroup

    with allowed_codes(404):
        gl.groups.delete(f"{group_for_function.full_path}/{subgroup_for_function.path}/{subsubgroup_name}")


@pytest.fixture(scope="function")
def shared_group_for_function(gl):
    group_name = get_random_name("shared_group")
    gitlab_group = create_group(group_name)

    yield gitlab_group

    with allowed_codes(404):
        gl.groups.delete(group_name)


class TestMembershipInheritance:
    def test__group_members_from_parent_group_are_not_added_directly_to_subgroup(
        self,
        gl,
        group_for_function,
        subgroup_for_function,
        users_for_function,
    ):
        inherited_user = users_for_function[0]

        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {inherited_user.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, group_for_function.full_path)

        refreshed_group = gl.groups.get(group_for_function.id)
        refreshed_subgroup = gl.groups.get(subgroup_for_function.id)

        root_group_direct_members = [member.username for member in refreshed_group.members.list(get_all=True)]
        subgroup_direct_members = [member.username for member in refreshed_subgroup.members.list(get_all=True)]

        assert inherited_user.username in root_group_direct_members
        assert inherited_user.username not in subgroup_direct_members

    def test__members_from_parent_group_are_not_added_directly_to_projects_in_subgroups(
        self,
        gl,
        group_for_function,
        users_for_function,
        root_and_subgroup_projects,
    ):
        inherited_user = users_for_function[0]
        _, subgroup_project = root_and_subgroup_projects

        group_for_function.members.create(
            {
                "user_id": inherited_user.id,
                "access_level": AccessLevel.DEVELOPER.value,
            }
        )

        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            members:
              users:
                {inherited_user.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, group_for_function.full_path)

        refreshed_subgroup_project = gl.projects.get(subgroup_project.id)

        subgroup_project_direct_members = [member.username for member in refreshed_subgroup_project.members.list()]
        subgroup_project_all_members = [member.username for member in refreshed_subgroup_project.members_all.list()]

        assert inherited_user.username not in subgroup_project_direct_members
        assert inherited_user.username in subgroup_project_all_members

    def test__group_member_groups_from_parent_group_are_not_shared_directly_to_descendants(
        self,
        gl,
        group_for_function,
        subgroup_for_function,
        shared_group_for_function,
    ):
        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              groups:
                {shared_group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, group_for_function.full_path)

        refreshed_group = gl.groups.get(group_for_function.id)
        refreshed_subgroup = gl.groups.get(subgroup_for_function.id)

        root_shared_with = {
            entry["group_full_path"]: entry["group_access_level"] for entry in refreshed_group.shared_with_groups
        }
        subgroup_shared_with = {
            entry["group_full_path"]: entry["group_access_level"] for entry in refreshed_subgroup.shared_with_groups
        }

        assert root_shared_with == {
            shared_group_for_function.full_path: AccessLevel.DEVELOPER.value,
        }
        assert shared_group_for_function.full_path not in subgroup_shared_with

    def test__group_member_groups_allow_explicit_deeper_override(
        self,
        gl,
        group_for_function,
        subgroup_for_function,
        nested_subgroup_for_function,
        shared_group_for_function,
    ):
        config = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              groups:
                {shared_group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
          {nested_subgroup_for_function.full_path}/*:
            group_members:
              groups:
                {shared_group_for_function.full_path}:
                  group_access: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, group_for_function.full_path)

        refreshed_group = gl.groups.get(group_for_function.id)
        refreshed_subgroup = gl.groups.get(subgroup_for_function.id)
        refreshed_nested_subgroup = gl.groups.get(nested_subgroup_for_function.id)

        root_shared_with = {
            entry["group_full_path"]: entry["group_access_level"] for entry in refreshed_group.shared_with_groups
        }
        subgroup_shared_with = {
            entry["group_full_path"]: entry["group_access_level"] for entry in refreshed_subgroup.shared_with_groups
        }
        nested_subgroup_shared_with = {
            entry["group_full_path"]: entry["group_access_level"]
            for entry in refreshed_nested_subgroup.shared_with_groups
        }

        assert root_shared_with == {
            shared_group_for_function.full_path: AccessLevel.DEVELOPER.value,
        }
        assert shared_group_for_function.full_path not in subgroup_shared_with
        assert nested_subgroup_shared_with == {
            shared_group_for_function.full_path: AccessLevel.MAINTAINER.value,
        }
