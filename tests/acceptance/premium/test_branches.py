import pytest
import time

from gitlab.v4.objects import ProjectProtectedBranch, User

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform
from tests.acceptance.conftest import create_project_member_developer

pytestmark = pytest.mark.requires_license


class TestBranches:

    def test__allow_user_ids(self, gl, project_for_function, branch_for_function):
        user_allowed_to_push = create_project_member_developer(gl, project_for_function)
        user_allowed_to_merge = create_project_member_developer(gl, project_for_function)
        user_allowed_to_push_and_merge = create_project_member_developer(gl, project_for_function)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        config_with_user_ids = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              {branch_for_function}:
                protected: true
                allowed_to_push:
                  - user_id: {user_allowed_to_push.id}
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user: {user_allowed_to_push_and_merge.username}
                allowed_to_merge:
                  - access_level: {AccessLevel.DEVELOPER.value} 
                  - user_id: {user_allowed_to_merge.id}
                  - user: {user_allowed_to_push_and_merge.username}
        """

        run_gitlabform(config_with_user_ids, project_for_function)

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
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == sorted(
            [
                user_allowed_to_push.id,
                user_allowed_to_push_and_merge.id,
            ]
        )
        assert merge_access_user_ids == sorted(
            [
                user_allowed_to_merge.id,
                user_allowed_to_push_and_merge.id,
            ]
        )

    def test__allow_more_than_one_user_by_ids(self, project_for_function, branch_for_function, gl):
        first_user = create_project_member_developer(gl, project_for_function)
        second_user = create_project_member_developer(gl, project_for_function)
        third_user = create_project_member_developer(gl, project_for_function)

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              {branch_for_function}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {first_user.id}
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

        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
                third_user.id,
            ]
        )
        assert merge_access_user_ids == []

    def test__branch_protection_dependent_on_members(
        self, project_for_function, group_for_function, branch_for_function, make_user, gl
    ):
        """
        Configure a branch protection setting that depends on users or groups (i.e. allowed_to_merge)
        Make sure the setting is applied successfully because users must be members
        before they can be configured in branch protection setting.
        """

        user_for_group_to_share_project_with = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)

        project_user_allowed_to_push = create_project_member_developer(gl, project_for_function)

        project_user_allowed_to_merge = create_project_member_developer(gl, project_for_function)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        config_branch_protection = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {user_for_group_to_share_project_with.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
          {project_for_function.path_with_namespace}:
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
              {branch_for_function}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {project_user_allowed_to_push.id}
                  - group_id: {group_for_function.id}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user: {project_user_allowed_to_merge.username}
                  - group_id: {group_for_function.id}
        """

        run_gitlabform(config_branch_protection, project_for_function)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            push_access_group_ids,
            merge_access_group_ids,
            _,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)

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

    def test__modifying_branch_protection_dependent_on_members(
        self, project_for_function, group_for_function, branch_for_function, make_user, gl
    ):
        """
        Configure a branch protection setting that depends on users or groups (i.e. allowed_to_merge)
        Make sure the setting is applied successfully because users must be members
        before they can be configured in branch protection setting.
        """

        user_for_group_to_share_project_with = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)

        project_user_allowed_to_push = create_project_member_developer(gl, project_for_function)

        project_user_allowed_to_merge = create_project_member_developer(gl, project_for_function)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        # Set Branch to be Protected before running gitlabform, as per:
        # https://github.com/gitlabform/gitlabform/issues/1061 and https://github.com/gitlabform/gitlabform/issues/1034
        # This should not result is gitlabform unprotected and reprotecting the branch in order to update config
        project_for_function.protectedbranches.create({"name": branch_for_function})

        config_branch_protection = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {user_for_group_to_share_project_with.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
          {project_for_function.path_with_namespace}:
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
              {branch_for_function}:
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

        run_gitlabform(config_branch_protection, project_for_function)

        protected_branch = project_for_function.protectedbranches.get(branch_for_function)
        assert protected_branch.allow_force_push is False
        assert protected_branch.code_owner_approval_required is False

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            push_access_group_ids,
            merge_access_group_ids,
            _,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)

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

    def test__modify_protection(self, project_for_function, group_for_function, branch_for_function, gl):
        """
        Set protection using the "standard" push_access_level fields, modify using the "Premium" allowed_to_push,
        and then revert back using "standard" level
        """
        project_user_allowed_to_push = create_project_member_developer(gl, project_for_function)

        project_user_allowed_to_merge = create_project_member_developer(gl, project_for_function)

        # Wait a little for newly created users to be available.
        time.sleep(2)

        # Protect branch using standard push_access_level fields
        config_standard_protect_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS.value}
                 merge_access_level: {AccessLevel.MAINTAINER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_standard_protect_branch, project_for_function.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        # Add manual approval rule on the protected branch
        protected_branch: ProjectProtectedBranch = project_for_function.protectedbranches.get(branch_for_function)
        project_for_function.approvalrules.create(
            {
                "name": "any",
                "approvals_required": 2,
                "rule_type": "regular",
                "protected_branch_ids": [
                    protected_branch.id,
                ],
            }
        )

        approval_rules = project_for_function.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "any"
        assert approval_rule.approvals_required == 2
        assert len(approval_rule.protected_branches) == 1
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id

        # Apply "Premium" allowed_to_push protection
        config_premium_protect_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {project_user_allowed_to_push.id}
                 allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user: {project_user_allowed_to_merge.username}
         """

        run_gitlabform(config_premium_protect_branch, project_for_function.path_with_namespace)

        protected_branch = project_for_function.protectedbranches.get(branch_for_function)
        assert protected_branch.allow_force_push is False
        assert protected_branch.code_owner_approval_required is False

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

        # If the branch was unprotected and then re-protected it should have a difference protected branch id after
        # the GLF run, and therefore will not match the protected_branch_ids array on the approval rule
        protected_branch: ProjectProtectedBranch = project_for_function.protectedbranches.get(branch_for_function)

        approval_rules = project_for_function.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "any"
        assert approval_rule.approvals_required == 2
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id

        # Reset to standard rules
        run_gitlabform(config_standard_protect_branch, project_for_function.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        # If the branch was unprotected and then re-protected it should have a difference protected branch id after
        # the GLF run, and therefore will not match the protected_branch_ids array on the approval rule
        protected_branch: ProjectProtectedBranch = project_for_function.protectedbranches.get(branch_for_function)

        approval_rules = project_for_function.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "any"
        assert approval_rule.approvals_required == 2
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id
