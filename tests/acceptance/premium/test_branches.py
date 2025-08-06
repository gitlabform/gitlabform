import pytest
import time

from gitlab import GitlabGetError
from gitlab.v4.objects import ProjectProtectedBranch, User

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform
from tests.acceptance.conftest import create_project_member

pytestmark = pytest.mark.requires_license


class TestBranches:

    def test__can_add_users_by_username_or_id_to_branch_protection_rules(
        self, project_for_function, branch_for_function, gl
    ):
        first_user = create_project_member(gl, project_for_function)
        second_user = create_project_member(gl, project_for_function)
        third_user = create_project_member(gl, project_for_function)

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              {branch_for_function}:
                protected: true
                allowed_to_push:
                  - user_id: {first_user.id}
                  - access_level: {AccessLevel.NO_ACCESS.value} 
                  - user_id: {second_user.id}
                  - user: {third_user.username}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_with_more_user_ids, project_for_function)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            _,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)

        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
                third_user.id,
            ]
        )
        assert merge_access_user_ids == []

    def test__can_add_users_and_group_to_branch_protection_rules(
        self, project, group_for_function, branch, make_user, gl
    ):
        """
        Configure a branch protection setting that depends on users or groups (i.e. allowed_to_merge)
        Make sure the setting is applied successfully because users must be members
        before they can be configured in branch protection setting.
        """
        user_for_group_to_share_project_with = make_user(AccessLevel.DEVELOPER, False)

        project_user_allowed_to_push = create_project_member(gl, project)

        project_user_allowed_to_merge = create_project_member(gl, project)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        try:
            protected_branch = project.protectedbranches.get(branch)
        except GitlabGetError:
            # Set Branch to be Protected before running gitlabform
            project.protectedbranches.create({"name": branch})

        config_branch_protection = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {user_for_group_to_share_project_with.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
          {project.path_with_namespace}:
            members:
              users:
                {project_user_allowed_to_push.username}:
                  access_level: developer
                {project_user_allowed_to_merge.username}:
                  access_level: developer
              groups:
                {group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {project_user_allowed_to_push.id}
                  - group_id: {group_for_function.id}
                allowed_to_merge:
                  - access_level: maintainer
                  - user: {project_user_allowed_to_merge.username}
                  - group_id: {group_for_function.id}
        """

        run_gitlabform(config_branch_protection, project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            push_access_group_ids,
            merge_access_group_ids,
            _,
        ) = get_only_branch_access_levels(project, branch)

        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert push_access_user_ids == sorted(
            [
                project_user_allowed_to_push.id,
            ]
        )
        assert push_access_group_ids == sorted(
            [
                group_for_function.id,
            ]
        )
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_user_ids == sorted(
            [
                project_user_allowed_to_merge.id,
            ]
        )
        assert merge_access_group_ids == sorted([group_for_function.id])

    def test__modify_protection_between_standard_and_premium_settings(self, project, group_for_function, branch, gl):
        """
        Set protection using the "standard" push_access_level fields, modify using the "Premium" feature allowed_to_push,
        and then revert back using "standard" features: https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
        """
        project_user_allowed_to_push = create_project_member(gl, project)

        project_user_allowed_to_merge = create_project_member(gl, project)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        # Protect branch using standard push_access_level fields
        config_standard_protect_branch = f"""
         projects_and_groups:
           {project.path_with_namespace}:
             branches:
               {branch}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS.value}
                 merge_access_level: {AccessLevel.MAINTAINER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_standard_protect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        # Apply "Premium" allowed_to_push protection
        config_premium_protect_branch = f"""
         projects_and_groups:
           {project.path_with_namespace}:
             branches:
               {branch}:
                 protected: true
                 allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {project_user_allowed_to_push.id}
                 allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user: {project_user_allowed_to_merge.username}
         """

        run_gitlabform(config_premium_protect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            _,
        ) = get_only_branch_access_levels(project, branch)

        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert push_access_user_ids == sorted(
            [
                project_user_allowed_to_push.id,
            ]
        )

        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_user_ids == sorted(
            [
                project_user_allowed_to_merge.id,
            ]
        )

        # Reset to standard rules
        run_gitlabform(config_standard_protect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
