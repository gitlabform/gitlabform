import pytest

from gitlab import GitlabGetError

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestGroupBranches:
    def test__create_group_protected_branch(self, group, project):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_branches:
              main:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, group)

        protected_branch = group.protectedbranches.get("main")
        assert protected_branch is not None

        push_levels = {
            r["access_level"]
            for r in protected_branch.push_access_levels
            if r.get("user_id") is None and r.get("group_id") is None
        }
        merge_levels = {
            r["access_level"]
            for r in protected_branch.merge_access_levels
            if r.get("user_id") is None and r.get("group_id") is None
        }

        assert AccessLevel.NO_ACCESS.value in push_levels
        assert AccessLevel.MAINTAINER.value in merge_levels

    def test__update_group_protected_branch(self, group, project):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_branches:
              main:
                protected: true
                push_access_level: {AccessLevel.DEVELOPER.value}
                merge_access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, group)

        protected_branch = group.protectedbranches.get("main")

        push_levels = {
            r["access_level"]
            for r in protected_branch.push_access_levels
            if r.get("user_id") is None and r.get("group_id") is None
        }
        merge_levels = {
            r["access_level"]
            for r in protected_branch.merge_access_levels
            if r.get("user_id") is None and r.get("group_id") is None
        }

        assert AccessLevel.DEVELOPER.value in push_levels
        assert AccessLevel.DEVELOPER.value in merge_levels

    def test__unprotect_group_branch(self, group, project):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_branches:
              main:
                protected: false
        """

        run_gitlabform(config, group)

        with pytest.raises(GitlabGetError):
            group.protectedbranches.get("main")

    def test__group_branch_protection_with_allow_force_push(self, group, project):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_branches:
              main:
                protected: true
                allow_force_push: true
                merge_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, group)

        protected_branch = group.protectedbranches.get("main")
        assert protected_branch.allow_force_push is True

        # Clean up
        protected_branch.delete()

    def test__group_branch_protection_idempotency(self, group, project):
        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_branches:
              main:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
        """

        # Run twice - second run should not error
        run_gitlabform(config, group)
        run_gitlabform(config, group)

        protected_branch = group.protectedbranches.get("main")
        assert protected_branch is not None

        # Clean up
        protected_branch.delete()
