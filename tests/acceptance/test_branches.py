import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    DEFAULT_README,
    get_gitlab,
    get_random_name,
)


gl = get_gitlab()


class TestBranches:
    def test__old_api(self, gitlab, group_and_project, branch):

        protect_branch_but_allow_all = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """
        run_gitlabform(protect_branch_but_allow_all, group_and_project)
        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is True
        assert the_branch["developers_can_merge"] is True

    # @pytest.mark.skipif(
    #     gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    # )
    # def test__code_owners_approval(self, gitlab, group_and_project, branch):
    #     branch_access_levels = gitlab.get_branch_access_levels(
    #         group_and_project, branch
    #     )
    #     assert branch_access_levels["code_owner_approval_required"] is False
    #
    #     protect_branch_with_code_owner_approval_required = f"""
    #     projects_and_groups:
    #       {group_and_project}:
    #         branches:
    #           {branch}:
    #             protected: true
    #             developers_can_push: false
    #             developers_can_merge: true
    #             code_owner_approval_required: true
    #     """
    #
    #     run_gitlabform(
    #         protect_branch_with_code_owner_approval_required, group_and_project
    #     )
    #
    #     branch_access_levels = gitlab.get_branch_access_levels(
    #         group_and_project, branch
    #     )
    #     assert branch_access_levels["code_owner_approval_required"] is True

    def test__old_api_other(self, gitlab, group_and_project, branch):

        protect_branch_and_disallow_all = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: false
                developers_can_merge: false
        """
        run_gitlabform(protect_branch_and_disallow_all, group_and_project)
        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is False
        assert the_branch["developers_can_merge"] is False

    def test__mixed_old_and_new_api(
        self,
        gitlab,
        group_and_project,
        branch,
        other_branch,
    ):
        mixed_config_with_access_levels = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              {other_branch}:
                protected: true
                push_access_level: {AccessLevel.DEVELOPER.value}
                merge_access_level: {AccessLevel.DEVELOPER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(mixed_config_with_access_levels, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is False
        assert the_branch["developers_can_merge"] is True

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, other_branch)
        assert push_access_levels == [AccessLevel.DEVELOPER.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__allow_user_ids(
        self,
        gitlab,
        group_and_project,
        branch,
        make_user,
    ):

        user_allowed_to_push = make_user(AccessLevel.DEVELOPER)
        user_allowed_to_merge = make_user(AccessLevel.DEVELOPER)
        user_allowed_to_push_and_merge = make_user(AccessLevel.DEVELOPER)

        config_with_user_ids = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - user_id: {user_allowed_to_push.id}
                  - access_level: {AccessLevel.NO_ACCESS.value}
                  - user: {user_allowed_to_push_and_merge.name}
                allowed_to_merge:
                  - access_level: {AccessLevel.DEVELOPER.value} 
                  - user_id: {user_allowed_to_merge.id}
                  - user: {user_allowed_to_push_and_merge.name}
        """

        run_gitlabform(config_with_user_ids, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)

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

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__allow_more_than_one_user_by_ids(
        self,
        gitlab,
        group_and_project,
        branch,
        make_user,
    ):
        first_user = make_user(AccessLevel.DEVELOPER)
        second_user = make_user(AccessLevel.DEVELOPER)
        third_user = make_user(AccessLevel.DEVELOPER)

        config_with_more_user_ids = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {first_user.id}
                  - user_id: {second_user.id}
                  - user: {third_user.name}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_with_more_user_ids, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)

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

    def test__old_api_then_new_api_and_unprotect(
        self, gitlab, group_and_project, branch
    ):

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is True
        assert the_branch["developers_can_merge"] is True

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is False

    def test__new_api_then_old_api_and_unprotect(
        self, gitlab, group_and_project, branch
    ):

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is True
        assert the_branch["developers_can_merge"] is True

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is False

    def test__unprotect_when_the_rest_of_the_parameters_are_still_specified_old_api(
        self, gitlab, group_and_project, branch
    ):

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True
        assert the_branch["developers_can_push"] is True
        assert the_branch["developers_can_merge"] is True

        config_unprotect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: false
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_unprotect_branch_with_old_api, group_and_project)

        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is False

    def test__unprotect_when_the_rest_of_the_parameters_are_still_specified_new_api(
        self, gitlab, group_and_project, branch
    ):

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_unprotect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: false
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_unprotect_branch_with_new_api, group_and_project)

        # old API
        branch = gitlab.get_branch(group_and_project, branch)
        assert branch["protected"] is False

        # new API
        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels is None
        assert merge_access_levels is None
        assert push_access_user_ids is None
        assert merge_access_user_ids is None
        assert unprotect_access_level is None

    def test__config_with_access_level_names(self, gitlab, group_and_project, branch):

        config_with_access_levels_names = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                push_access_level: no_access        # note "_" or " " and the various
                merge_access_level: Developer       # case in each line. it should not
                unprotect_access_level: MAINTAINER  # matter as we allow any case.
        """

        run_gitlabform(config_with_access_levels_names, group_and_project)

        (
            push_access_level,
            merge_access_level,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_level == [AccessLevel.NO_ACCESS.value]
        assert merge_access_level == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
