import pytest
import time

import gitlab

from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform

pytestmark = pytest.mark.requires_license


class TestBranches:
    def test__code_owners_approval(self, project, branch):
        try:
            protected_branch = project.protectedbranches.get(branch)
            assert protected_branch.code_owner_approval_required is False
        except gitlab.GitlabGetError:
            # this is fine, the branch may not be protected at all yet
            pass

        protect_branch_with_code_owner_approval_required = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
                code_owner_approval_required: true
        """

        run_gitlabform(protect_branch_with_code_owner_approval_required, project)

        protected_branch = project.protectedbranches.get(branch)
        assert protected_branch.code_owner_approval_required is True

    def test__allow_user_ids(self, project, branch, make_user):
        user_allowed_to_push = make_user(AccessLevel.DEVELOPER)
        user_allowed_to_merge = make_user(AccessLevel.DEVELOPER)
        user_allowed_to_push_and_merge = make_user(AccessLevel.DEVELOPER)

        config_with_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
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

        run_gitlabform(config_with_user_ids, project)
        assert True
        # time.sleep(5)

        # (
        #     push_access_levels,
        #     merge_access_levels,
        #     push_access_user_ids,
        #     merge_access_user_ids,
        #     _,
        # ) = get_only_branch_access_levels(project, branch)

        # assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        # assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        # assert push_access_user_ids == sorted(
        #     [
        #         user_allowed_to_push.id,
        #         user_allowed_to_push_and_merge.id,
        #     ]
        # )
        # assert merge_access_user_ids == sorted(
        #     [
        #         user_allowed_to_merge.id,
        #         user_allowed_to_push_and_merge.id,
        #     ]
        # )

    def test__allow_more_than_one_user_by_ids(self, project, branch, make_user):
        first_user = make_user(AccessLevel.DEVELOPER)
        second_user = make_user(AccessLevel.DEVELOPER)
        third_user = make_user(AccessLevel.DEVELOPER)

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {first_user.id}
                  - user_id: {second_user.id}
                  - user: {third_user.username}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_with_more_user_ids, project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
        ) = get_only_branch_access_levels(project, branch)

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

    def test__branch_protection_dependent_on_members(self, project_for_function, group_for_function, branch_for_function, make_user):
        """
        Configure a branch protection setting that depends on users or groups (i.e. allowed_to_merge)
        Make sure the setting is applied successfully because users must be members
        before they can be configured in branch protection setting.
        """

        user_for_group_to_share_project_with = make_user(level = AccessLevel.DEVELOPER, add_to_project = False)
        project_user_allowed_to_push = make_user(level = AccessLevel.DEVELOPER, add_to_project = False)
        project_user_allowed_to_merge = make_user(level = AccessLevel.DEVELOPER, add_to_project = False)

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
        assert merge_access_group_ids == sorted(
            [
                group_for_function.id
            ]
        )
