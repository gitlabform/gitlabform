import logging

import pytest
import time

from gitlab import GitlabGetError
from gitlab.v4.objects import ProjectProtectedBranch, User

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform
from tests.acceptance.conftest import create_project_member

pytestmark = pytest.mark.requires_license


class TestBranches:

    @pytest.fixture(scope="class")
    def three_maintainers(self, gl, project):
        """
        Creates three project members once per class to be used across multiple tests.
        This avoids redundant user creation and email conflicts.
        """
        first_user = create_project_member(gl, project, AccessLevel.MAINTAINER.value)
        second_user = create_project_member(gl, project, AccessLevel.MAINTAINER.value)
        third_user = create_project_member(gl, project, AccessLevel.MAINTAINER.value)
        time.sleep(5)  # Increased wait for memberships to propagate in slow environments
        return first_user, second_user, third_user

    def test__modify_force_push_and_code_owner_approvals(self, project, branch):
        """
        Tests the modification of boolean branch protection flags:
        'allow_force_push' and 'code_owner_approval_required'.

        It validates that these settings can be toggled and that omitting them
        in subsequent runs does not reset them (additive/raw parameter design).
        """
        try:
            protected_branch = project.protectedbranches.get(branch)
            protected_branch.delete()
        except GitlabGetError:
            # Branch currently not protected so do nothing
            logging.debug("Nothing to reset")

        config_protect_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allow_force_push: false
                code_owner_approval_required: true
        """

        run_gitlabform(config_protect_branch, project.path_with_namespace)

        protected_branch = project.protectedbranches.get(branch)
        assert protected_branch.allow_force_push is False
        assert protected_branch.code_owner_approval_required is True

        config_modify_settings_for_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allow_force_push: true
                code_owner_approval_required: false
        """

        run_gitlabform(config_modify_settings_for_branch, project.path_with_namespace)

        protected_branch = project.protectedbranches.get(branch)
        assert protected_branch.allow_force_push is True
        assert protected_branch.code_owner_approval_required is False

        config_remove_settings_for_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
        """

        run_gitlabform(config_remove_settings_for_branch, project.path_with_namespace)

        # If config is no longer defined, GitlabForm should not make any changes
        protected_branch = project.protectedbranches.get(branch)
        assert protected_branch.allow_force_push is True
        assert protected_branch.code_owner_approval_required is False

    def test__can_add_users_by_username_or_id_to_branch_protection_rules(self, project, branch, three_maintainers):
        """
        Validates that users can be added to branch protection rules (allowed_to_push/merge)
        using both their numeric GitLab IDs and their usernames.
        """

        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        first_user, second_user, third_user = three_maintainers

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - user_id: {first_user.id}
                  - access_level: {AccessLevel.NO_ACCESS.value} 
                  - user_id: {second_user.id}
                  - user: {third_user.username}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user_id: {third_user.id}
                  - user: {second_user.username}
        """

        run_gitlabform(config_with_more_user_ids, project.path_with_namespace)

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
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
                third_user.id,
            ]
        )
        assert merge_access_user_ids == sorted(
            [
                second_user.id,
                third_user.id,
            ]
        )

    def test__branch_protection_idempotency_with_users_and_roles(self, project, branch, three_maintainers):
        """
        Tests that branch protection is idempotent when mixing specific users and roles.

        Specifically checks scenarios where a user is explicitly listed but also
        already has access via a role-based rule (e.g., Maintainer role).
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        first_user, second_user, third_user = three_maintainers

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - user: {first_user.username}
                  - user: {second_user.username}
                allowed_to_merge:
                  - user: {third_user.username}
                  - access_level: maintainer
                allowed_to_unprotect:
                  - access_level: maintainer
        """

        # 1. First run
        run_gitlabform(config_with_more_user_ids, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)

        assert unprotect_access_level == AccessLevel.MAINTAINER.value
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_user_ids == sorted([third_user.id])
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
            ]
        )

        # 2. Second run (Idempotency check)
        # This step previously failed for redundant user/role rules due to incorrect matching logic.
        run_gitlabform(config_with_more_user_ids, project.path_with_namespace)

        (
            push_access_levels_after,
            merge_access_levels_after,
            push_access_user_ids_after,
            merge_access_user_ids_after,
            _,
            _,
            unprotect_access_level_after,
        ) = get_only_branch_access_levels(project, branch)

        assert push_access_levels_after == push_access_levels
        assert merge_access_levels_after == merge_access_levels
        assert push_access_user_ids_after == push_access_user_ids
        assert merge_access_user_ids_after == merge_access_user_ids
        assert unprotect_access_level_after == unprotect_access_level

    def test__users_are_not_removed_from_branch_protection_rules_by_omission(self, project, branch, three_maintainers):
        """
        Validates the additive design for user-based protection rules.

        Checks that when some users are explicitly configured in the rules,
        other users previously configured in GitLab are NOT removed (they persist).
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        first_user, second_user, third_user = three_maintainers

        # Add all users as allowed to push
        project.protectedbranches.create(
            {
                "name": branch,
                "allowed_to_merge": [{"access_level": AccessLevel.MAINTAINER.value}],
                "allowed_to_push": [
                    {"user_id": first_user.id},
                    {"user_id": second_user.id},
                    {"user_id": third_user.id},
                ],
                "allowed_to_unprotect": [{"access_level": AccessLevel.MAINTAINER.value}],
            }
        )

        # Wait for the rule creation to be ready in the API
        time.sleep(2)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)

        assert unprotect_access_level == AccessLevel.MAINTAINER.value
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
                third_user.id,
            ]
        )
        assert len(merge_access_user_ids) == 0

        # Remove second_user from being allowed to push
        config_with_more_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_merge:
                  - access_level: maintainer
                allowed_to_unprotect:
                  - access_level: maintainer
                allowed_to_push:
                  - user: {first_user.username}
                  - user: {third_user.username}
        """

        run_gitlabform(config_with_more_user_ids, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)

        assert unprotect_access_level == AccessLevel.MAINTAINER.value
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,  # Additive design: omitted user should still be present
                third_user.id,
            ]
        )
        assert len(merge_access_user_ids) == 0

    def test__can_add_users_and_group_to_branch_protection_rules(
        self, project, group_for_function, branch, make_user, gl, three_maintainers
    ):
        """
        Tests that branch protection rules can be configured using a mix of
        users (by ID or username) and groups.

        Also verifies that GitLabForm handles the dependency where users/groups
        must be members of the project before they can be added to protection rules.
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        user_for_group_to_share_project_with = make_user(AccessLevel.DEVELOPER, False)

        first_user, second_user, _ = three_maintainers

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
                {first_user.username}:
                  access_level: maintainer
                {second_user.username}:
                  access_level: maintainer
              groups:
                {group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user_id: {first_user.id}
                  - group_id: {group_for_function.id}
                allowed_to_merge:
                  - access_level: maintainer
                  - user: {second_user.username}
                  - group_id: {group_for_function.id}
        """

        run_gitlabform(config_branch_protection, project.path_with_namespace)

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
                first_user.id,
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
                second_user.id,
            ]
        )
        assert merge_access_group_ids == sorted([group_for_function.id])

    def test__modify_protection_between_standard_and_premium_settings(self, project, branch, three_maintainers):
        """
        Tests switching between standard role-based protection (e.g., push_access_level)
        and premium entity-based protection (e.g., allowed_to_push).

        Validates that entities added in premium steps are retained during standard updates (additive).
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        first_user, second_user, _ = three_maintainers

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

        config_premium_protect_branch = f"""
         projects_and_groups:
           {project.path_with_namespace}:
             branches:
               {branch}:
                 protected: true
                 allowed_to_push:
                  - access_level: no access
                  - user_id: {first_user.id}
                 allowed_to_merge:
                  - access_level: maintainer
                  - user: {second_user.username}
         """

        # 1. First run: Apply Premium protection (user-based)
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
                first_user.id,
            ]
        )

        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_user_ids == sorted(
            [
                second_user.id,
            ]
        )

        # 2. Second run: Switch back to Standard rules (role-based)
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
        # Verify entities (users) are STILL present because the standard run was additive
        assert sorted(push_access_user_ids) == sorted([first_user.id])
        assert sorted(merge_access_user_ids) == sorted([second_user.id])
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__if_protected_branch_config_does_not_change_then_branch_approval_rules_are_retained(self, project, branch):
        """
        Tests that manual MR approval rules attached to a protected branch are retained
        when GitLabForm runs with an unchanged branch protection configuration.

        This ensures that GitLabForm doesn't redundantly unprotect/reprotect branches,
        which would clear these rules (loss of state).
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        # Previously we have unprotected and re-protected branches in order to apply config changes
        # and even if config did not change, branches_processor would thing it still needed a change.
        # This resulted in loss of manual approval rules: https://github.com/gitlabform/gitlabform/issues/1061
        # This test can check that branch protection is not modified when the config is unchanged between glf runs
        # when run in debug mode with breakpoints from an IDE, and validates the branch approval rules being retained
        config_protect_branch = f"""
         projects_and_groups:
           {project.path_with_namespace}:
             branches:
               {branch}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS.value}
                 merge_access_level: {AccessLevel.MAINTAINER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_protect_branch, project.path_with_namespace)

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

        # Add manual approval rule on the protected branch
        protected_branch = project.protectedbranches.get(branch)

        project.approvalrules.create(
            {
                "name": "Branch Protection validation",
                "approvals_required": 2,
                "rule_type": "regular",
                "protected_branch_ids": [
                    protected_branch.id,
                ],
            }
        )

        approval_rules = project.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "Branch Protection validation"
        assert approval_rule.approvals_required == 2
        assert len(approval_rule.protected_branches) == 1
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id

        # re-run the exact same config
        run_gitlabform(config_protect_branch, project.path_with_namespace)

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

        # If the branch was unprotected and then re-protected the branch id of the protected branch would likely differ
        # from that stored in the branch approval rule
        protected_branch = project.protectedbranches.get(branch)

        approval_rules = project.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "Branch Protection validation"
        assert approval_rule.approvals_required == 2
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id

    def test__can_add_deploy_key_to_branch_protection_rules(
        self, project, branch, public_ssh_key, other_public_ssh_key
    ):
        """
        Tests that deploy keys can be added to branch protection rules (allowed_to_push).
        This test specifically validates the additive nature of deploy key rules
        and ensures that existing deploy keys are not removed when new ones are added.
        """
        # Reset branch protection state to ensure idempotency and prevent interference
        try:
            project.protectedbranches.get(branch).delete()
        except GitlabGetError:
            pass

        # Create two deploy keys with push access
        deploy_key_1 = project.keys.create(
            {
                "title": "test-deploy-key-1",
                "key": public_ssh_key,
                "can_push": True,
            }
        )
        deploy_key_2 = project.keys.create(
            {
                "title": "test-deploy-key-2",
                "key": other_public_ssh_key,
                "can_push": True,
            }
        )

        # 1. Protect the branch initially without the deploy key
        initial_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.MAINTAINER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
        """
        run_gitlabform(initial_config, project.path_with_namespace)

        # 2. Update the protection to include the first deploy key
        config_with_deploy_key_1 = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - deploy_key_id: {deploy_key_1.id}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """
        run_gitlabform(config_with_deploy_key_1, project.path_with_namespace)

        protected_branch = project.protectedbranches.get(branch)
        push_access_levels = protected_branch.push_access_levels
        found_deploy_key_1 = any(access.get("deploy_key_id") == deploy_key_1.id for access in push_access_levels)
        assert found_deploy_key_1 is True, "First deploy key should have been added during update"

        # 3. Update the protection to include the second deploy key (additive check)
        config_with_deploy_key_2 = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - deploy_key_id: {deploy_key_2.id}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """
        run_gitlabform(config_with_deploy_key_2, project.path_with_namespace)

        protected_branch = project.protectedbranches.get(branch)
        push_access_levels = protected_branch.push_access_levels
        found_deploy_key_1 = any(access.get("deploy_key_id") == deploy_key_1.id for access in push_access_levels)
        found_deploy_key_2 = any(access.get("deploy_key_id") == deploy_key_2.id for access in push_access_levels)

        assert found_deploy_key_1 is True, "First deploy key should still be present (additive design)"
        assert found_deploy_key_2 is True, "Second deploy key should have been added"
