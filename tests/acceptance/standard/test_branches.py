import pytest
import time

from gitlab import GitlabGetError

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform


@pytest.mark.ce
class TestBranches:
    def test__not_supplying_protected_keyword(self, project, branch):
        config_protect_branch = f"""
           projects_and_groups:
             {project.path_with_namespace}:
               branches:
                 {branch}:
                   push_access_level: {AccessLevel.NO_ACCESS.value}
                   merge_access_level: {AccessLevel.MAINTAINER.value}
                   unprotect_access_level: {AccessLevel.MAINTAINER.value}
           """

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            run_gitlabform(config_protect_branch, project.path_with_namespace)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test__can_protect_and_unprotect_a_branch(self, project, branch, is_enterprise_edition):
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
        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

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

    def test__repeatedly_modify_protection_rules(
        self, project_for_function, branch_for_function, is_enterprise_edition
    ):
        """
        This test modifies the branch protection rules multiple times using gitlabform to stress the "Update" functionality.

        If we were to run the config only once or twice we would test "Create" once and "Update" once, to have confidence
        that the "Update" functionality can swap between different states without breaking we need to "Update" repeatedly

        Usually we prefer **not** to run multiple iterations of gitlabform in an integration test
        """
        try:
            project_for_function.protectedbranches.get(branch_for_function)
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
            _,
            _,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]

        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

        # Re run the configuration with NO ACCESS to push, MAINTAINER to unprotect, but not supplying merge_access_level
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
            _,
            _,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]

        if is_enterprise_edition:
            # In EE our update strategy should retain the previously defined merge_access_level even though
            # it was removed from config
            assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        else:
            # In CE, due to: https://gitlab.com/rluna-gitlab/gitlab-ce/-/work_items/37, we unprotect and reprotect
            # a branch to apply changes. Therefore, merge_access_levels should be not None but we don't want to tie our
            # tests to GitLab's defaults in case those change underneath us
            assert merge_access_levels[0] is not None

        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

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
            _,
            _,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

    def test__protect_with_wildcard(self, project, is_enterprise_edition):
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
        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

        wildcard_matching_branch = project.branches.create({"branch": "r-1", "ref": "main"})
        assert wildcard_matching_branch.protected is True

    def test__can_protect_a_branch_when_defining_only_one_access_level(
        self, project_for_function, branch_for_function, is_enterprise_edition
    ):
        """
        GitLab API exposes the ability to protect a branch with push_access_level, merge_access_level and
        unprotect_access_level. However these are all optional, so we should test that we can still protect
        and update a branches protection rules when only defining one access level (the others will be set to
        whatever defaults GitLab's API implementation applies, which we don't test here to avoid tightly coupling to
        implementation outside our control).
        """
        # Initial state
        initial_state_config = f"""
          projects_and_groups:
            {project_for_function.path_with_namespace}:
              branches:
                {branch_for_function}:
                 protected: true
                 allow_force_push: false
                 push_access_level: no access
          """
        run_gitlabform(initial_state_config, project_for_function.path_with_namespace)

        protected_branch = project_for_function.protectedbranches.get(branch_for_function)
        assert protected_branch.attributes.get("allow_force_push") is False

        (
            push_access_levels,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        # We set Push Access Level to No Access
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]

        # Update push_access_level to Maintainer
        config_protect_branch = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              {branch_for_function}:
               protected: true
               allow_force_push: false
               push_access_level: maintainer
        """

        run_gitlabform(config_protect_branch, project_for_function.path_with_namespace)

        protected_branch = project_for_function.protectedbranches.get(branch_for_function)
        assert protected_branch.attributes.get("allow_force_push") is False

        (
            push_access_levels,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = get_only_branch_access_levels(project_for_function, branch_for_function)
        # We set Push Access Level to Maintainer
        assert push_access_levels == [AccessLevel.MAINTAINER.value]

    def test__config_with_access_level_names(self, project, branch, is_enterprise_edition):
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
        if is_enterprise_edition:
            assert unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert unprotect_access_level is None

    def test__can_choose_not_to_inherit_branch_protections_from_parent_group(
        self,
        group,
        project_for_function,
        branch_for_function,
        other_branch_for_function,
        is_enterprise_edition,
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

        # branch_for_function should exist on the project, but be unprotected as the protection rules
        # are only defined at the group level, which the project is not inheriting
        try:
            branch = project_for_function.branches.get(branch_for_function)
            assert branch is not None
        except GitlabGetError:
            pytest.fail(f"Expected {branch_for_function} to exist on Project")

        protected_branches = project_for_function.protectedbranches.list()
        for pb in protected_branches:
            assert pb.name != branch_for_function

        # other_branch_for_function should be protected as it's protection rules are defined at the
        # project level
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
        if is_enterprise_edition:
            assert other_branch_unprotect_access_level is AccessLevel.MAINTAINER.value
        else:
            assert other_branch_unprotect_access_level is None
