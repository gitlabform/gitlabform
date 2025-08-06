from gitlab import GitlabGetError
from gitlab.v4.objects import ProjectProtectedBranch

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform


class TestBranches:
    def test__can_protect_and_unprotect_a_branch(self, project, branch):
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

        config_unprotect_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: false
        """

        run_gitlabform(config_unprotect_branch, project.path_with_namespace)

        # Verify branch is no longer one of the project's protected branches
        protected_branches = project.protectedbranches.list()
        for pb in protected_branches:
            assert pb.name != branch

    def test__modify_force_push_and_code_owner_approvals(self, project, branch):
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

        # If we were protecting a branch for the first time and not passing these values, Gitlab would default both
        # to "False" as per: https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
        # We retain that decision-making rather than leaving the values at their previous state, otherwise
        # if a User manually unprotected a branch, and restored protection by re-running Gitlabform, the flags would
        # have silently changed
        protected_branch = project.protectedbranches.get(branch)
        assert protected_branch.allow_force_push is False
        assert protected_branch.code_owner_approval_required is False

    def test__repeatedly_modify_protection_rules(self, project_for_function, branch_for_function):
        """
        This test modifies the branch protection rules multiple times using gitlabform to stress the "Update" functionality.

        If we were to run the config only once or twice we would test "Create" once and "Update" once, to have confidence
        that the "Update" functionality can swap between different states without breaking we need to "Update" repeatedly

        Usually we prefer **not** to run multiple iterations of gitlabform in an integration test
        """

        try:
            protected_branch = project_for_function.protectedbranches.get(branch_for_function)
        except GitlabGetError:
            # Set Branch to be Protected before running gitlabform
            project_for_function.protectedbranches.create({"name": branch_for_function})

        # Initially update branch with NO ACCESS to push, MAINTAINER to unprotect and DEVELOPER to merge
        config_protect_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS.value}
                 merge_access_level: {AccessLevel.DEVELOPER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_protect_branch, project_for_function.path_with_namespace)

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
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        # Re run the configuration with NO ACCESS to push, MAINTAINER to unprotect, but MAINTAINER not supplied
        config_without_merge_access_level_defined = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_without_merge_access_level_defined, project_for_function.path_with_namespace)

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

        # When first protecting a branch, if merge_access_level is not supplied, Gitlab will default to "Maintainer"
        # https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
        # We retain that functionality, if a user no longer defines a given access_level we default back to "Maintainer"
        # otherwise if a User manually unprotected a branch, and restored protection by re-running Gitlabform, the
        # access_level would silently change
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        # Re run the configuration with MAINTAINER to push, MAINTAINER to unprotect and MAINTAINER to merge
        config_remodify_protection_on_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.MAINTAINER.value}
                 merge_access_level: {AccessLevel.MAINTAINER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_remodify_protection_on_branch, project_for_function.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__if_protected_branch_config_does_not_change_then_branch_approval_rules_are_retained(self, project, branch):
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
        protected_branch: ProjectProtectedBranch = project.protectedbranches.get(branch)
        project.approvalrules.create(
            {
                "name": "any",
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
        assert approval_rule.name == "any"
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
        protected_branch: ProjectProtectedBranch = project.protectedbranches.get(branch)

        approval_rules = project.approvalrules.list(get_all=True)
        assert len(approval_rules) == 1
        approval_rule = approval_rules[0]
        assert approval_rule.name == "any"
        assert approval_rule.approvals_required == 2
        pb_ar = approval_rule.protected_branches[0]
        assert pb_ar.get("id") == protected_branch.id

    def test__protect_with_wildcard(self, project):
        branch_wildcard = "r-*"
        config_protect_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              "{branch_wildcard}":
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
        ) = get_only_branch_access_levels(project, branch_wildcard)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        wildcard_matching_branch = project.branches.create({"branch": "r-1", "ref": "main"})
        assert wildcard_matching_branch.protected is True

    def test__config_with_access_level_names(self, project, branch):
        config_with_access_levels_names = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: no_access        # note "_" or " " and the various
                merge_access_level: Developer       # case in each line. it should not
                unprotect_access_level: MAINTAINER  # matter as we allow any case.
        """

        run_gitlabform(config_with_access_levels_names, project.path_with_namespace)

        (
            push_access_level,
            merge_access_level,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_level == [AccessLevel.NO_ACCESS.value]
        assert merge_access_level == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__can_choose_not_to_inherit_branch_protections_from_parent_group(
        self,
        group,
        project_for_function,
        branch_for_function,
        other_branch_for_function,
    ):
        # project will be created in the group by the fixture in conftest.py
        # branches will be created on the project by the fixtures
        config_yaml = f"""
        projects_and_groups:
          {group.full_path}/*:
            branches:   
              {branch_for_function}:
                protected: true
                push_access_level: developer
                merge_access_level: developer
                unprotect_access_level: maintainer

          {project_for_function.path_with_namespace}:
            branches:
              inherit: false
              {other_branch_for_function}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
        """

        run_gitlabform(config_yaml, project_for_function.path_with_namespace)

        (
            push_access_level,
            merge_access_level,
            _,
            _,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_level is None
        assert merge_access_level is None
        assert unprotect_access_level is None

        (
            other_branch_push_access_level,
            other_branch_merge_access_level,
            _,
            _,
            _,
            _,
            other_branch_unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, other_branch_for_function)
        assert other_branch_push_access_level == [AccessLevel.MAINTAINER.value]
        assert other_branch_merge_access_level == [AccessLevel.DEVELOPER.value]
        assert other_branch_unprotect_access_level is AccessLevel.MAINTAINER.value
