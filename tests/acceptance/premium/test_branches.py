import pytest

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

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
        ) = get_only_branch_access_levels(project, branch)

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
