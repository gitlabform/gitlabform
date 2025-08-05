import time

from gitlab.v4.objects import ProjectProtectedBranch

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform


class TestBranches:
    def test__protect_and_unprotect(self, project, branch):
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
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_unprotect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels is None
        assert merge_access_levels is None
        assert push_access_user_ids is None
        assert merge_access_user_ids is None
        assert unprotect_access_level is None

    def test__modify_protection(self, project_for_function, branch_for_function):
        config_protect_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.NO_ACCESS}
                 merge_access_level: {AccessLevel.MAINTAINER.value}
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
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_modify_protection_on_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.MAINTAINER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER}
         """

        run_gitlabform(config_modify_protection_on_branch, project_for_function.path_with_namespace)

        # Wait a little for Gitlab update PATCH api processing
        time.sleep(2)

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
        # If it is not defined in create or update, Gitlab defaults to "Maintainer" level
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_remodify_protection_on_branch = f"""
         projects_and_groups:
           {project_for_function.path_with_namespace}:
             branches:
               {branch_for_function}:
                 protected: true
                 push_access_level: {AccessLevel.MAINTAINER.value}
                 merge_access_level: {AccessLevel.DEVELOPER.value}
                 unprotect_access_level: {AccessLevel.MAINTAINER.value}
         """

        run_gitlabform(config_remodify_protection_on_branch, project_for_function.path_with_namespace)

        # Wait a little for Gitlab update PATCH api processing
        time.sleep(2)

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
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
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

        # If the branch was unprotected and then re-protected it should have a difference protected branch id after
        # the GLF run, and therefore will not match the protected_branch_ids array on the approval rule
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
