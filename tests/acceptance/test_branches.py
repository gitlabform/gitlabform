import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    DEFAULT_README,
    get_gitlab,
)


gl = get_gitlab()


@pytest.fixture(scope="function")
def branches(request, gitlab, group_and_project):
    branches = [
        "protect_branch_but_allow_all",
        "protect_branch_with_code_owner_approval_required",
        "protect_branch_and_disallow_all",
        "protect_branch_and_allow_merges",
        "protect_branch_and_allow_pushes",
        "protect_branch_and_allow_merges_access_levels",
        "protect_branch_and_allow_pushes_access_levels",
        "protect_branch_and_allowed_to_push",
        "protect_branch_and_allowed_to_merge",
        "protect_branch_and_allow_access_levels_with_user_ids",
        "protect_branch",
    ]
    for branch in branches:
        gitlab.create_branch(group_and_project, branch, "main")

    def fin():
        for branch in branches:
            gitlab.delete_branch(group_and_project, branch)

        gitlab.set_file(
            group_and_project,
            "main",
            "README.md",
            DEFAULT_README,
            "Reset default content",
        )

    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def one_maintainer_and_two_developers(gitlab, group_and_project, users):

    gitlab.add_member_to_project(
        group_and_project, users[0], AccessLevel.MAINTAINER.value
    )
    gitlab.add_member_to_project(
        group_and_project, users[1], AccessLevel.DEVELOPER.value
    )
    gitlab.add_member_to_project(
        group_and_project, users[2], AccessLevel.DEVELOPER.value
    )

    yield group_and_project

    # we try to remove all users, not just the 3 added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_project(group_and_project, user)


class TestBranches:
    def test__protect_branch_but_allow_all(self, gitlab, group_and_project, branches):

        protect_branch_but_allow_all = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_but_allow_all:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """
        run_gitlabform(protect_branch_but_allow_all, group_and_project)
        branch = gitlab.get_branch(group_and_project, "protect_branch_but_allow_all")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

    # @pytest.mark.skipif(
    #     gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    # )
    # def test__code_owners_approval(self, gitlab, group_and_project, branches):
    #     group_and_project = group_and_project
    #
    #     branch_access_levels = gitlab.get_branch_access_levels(
    #         group_and_project, "protect_branch_but_allow_all"
    #     )
    #     assert branch_access_levels["code_owner_approval_required"] is False
    #
    #     protect_branch_with_code_owner_approval_required = f"""
    #     projects_and_groups:
    #       {group_and_project}:
    #         branches:
    #           protect_branch_with_code_owner_approval_required:
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
    #         group_and_project, "protect_branch_with_code_owner_approval_required"
    #     )
    #     assert branch_access_levels["code_owner_approval_required"] is True

    def test__protect_branch_and_disallow_all(
        self, gitlab, group_and_project, branches
    ):

        protect_branch_and_disallow_all = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_disallow_all:
                protected: true
                developers_can_push: false
                developers_can_merge: false
        """
        run_gitlabform(protect_branch_and_disallow_all, group_and_project)
        branch = gitlab.get_branch(group_and_project, "protect_branch_and_disallow_all")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is False
        assert branch["developers_can_merge"] is False

    def test__mixed_config(self, gitlab, group_and_project, branches):

        mixed_config = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_merges:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protect_branch_and_allow_pushes:
                protected: true
                developers_can_push: true
                developers_can_merge: false
        """
        run_gitlabform(mixed_config, group_and_project)
        branch = gitlab.get_branch(group_and_project, "protect_branch_and_allow_merges")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is False
        assert branch["developers_can_merge"] is True

        branch = gitlab.get_branch(group_and_project, "protect_branch_and_allow_pushes")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is False

        unprotect_branches = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_merges:
                protected: false
              protect_branch_and_allow_pushes:
                protected: false
        """
        run_gitlabform(unprotect_branches, group_and_project)

        for branch in [
            "protect_branch_and_allow_merges",
            "protect_branch_and_allow_pushes",
        ]:
            branch = gitlab.get_branch(group_and_project, branch)
            assert branch["protected"] is False

    def test__mixed_config_with_new_api(
        self,
        gitlab,
        group_and_project,
        branches,
        users,
        one_maintainer_and_two_developers,
    ):
        mixed_config_with_access_levels = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.DEVELOPER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
              '*_allow_pushes_access_levels':
                protected: true
                push_access_level: {AccessLevel.DEVELOPER.value}
                merge_access_level: {AccessLevel.DEVELOPER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(mixed_config_with_access_levels, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "protect_branch_and_allow_merges_access_levels"
        )
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "*_allow_pushes_access_levels"
        )
        assert push_access_levels == [AccessLevel.DEVELOPER.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        mixed_config_with_access_levels_update = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
              '*_allow_pushes_access_levels':
                protected: true
                push_access_level: {AccessLevel.MAINTAINER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(mixed_config_with_access_levels_update, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "protect_branch_and_allow_merges_access_levels"
        )
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "*_allow_pushes_access_levels"
        )
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        mixed_config_with_access_levels_unprotect_branches = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: false
              '*_allow_pushes_access_levels':
                protected: false
        """

        run_gitlabform(
            mixed_config_with_access_levels_unprotect_branches, group_and_project
        )

        for branch in [
            "protect_branch_and_allow_merges_access_levels",
            "protect_branch_and_allow_pushes_access_levels",
        ]:
            branch = gitlab.get_branch(group_and_project, branch)
            assert branch["protected"] is False

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__allow_user_ids(
        self,
        gitlab,
        group_and_project,
        branches,
        users,
        one_maintainer_and_two_developers,
    ):

        user_allowed_to_push_id = gitlab.get_user_to_protect_branch(users[0])
        user_allowed_to_merge_id = gitlab.get_user_to_protect_branch(users[1])
        user_allowed_to_push_and_allowed_to_merge_id = (
            gitlab.get_user_to_protect_branch(users[2])
        )

        # testing allowed_to_push  and allowed_to_merge for user support on protect branch (gitlab premium feature)
        mixed_config_with_allowed_to_push_and_merge = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allowed_to_merge:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value} 
                allowed_to_merge:
                  - access_level: {AccessLevel.DEVELOPER.value} 
                  - user_id: {user_allowed_to_merge_id}
                  - user: {users[2]}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
              '*_and_allowed_to_push':
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.DEVELOPER.value} 
                  - user_id: {user_allowed_to_push_id}
                  - user: {users[1]} 
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(mixed_config_with_allowed_to_push_and_merge, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "protect_branch_and_allowed_to_merge"
        )

        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]

        current_push_access_user_ids = []
        current_push_access_user_ids.sort()
        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = [
            user_allowed_to_merge_id,
            user_allowed_to_push_and_allowed_to_merge_id,
        ]
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids

        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "*_and_allowed_to_push"
        )

        assert push_access_levels == [AccessLevel.DEVELOPER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]

        current_push_access_user_ids = [
            user_allowed_to_push_id,
            user_allowed_to_merge_id,
        ]
        current_push_access_user_ids.sort()
        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = []
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids

        assert unprotect_access_level is AccessLevel.DEVELOPER.value

        mixed_config_with_allowed_to_push_and_merge_update = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allowed_to_merge:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.NO_ACCESS.value} 
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {user_allowed_to_merge_id}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
              '*_and_allowed_to_push':
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {user_allowed_to_push_id}
                  - user: {users[2]}
                  - user: {users[1]} 
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(
            mixed_config_with_allowed_to_push_and_merge_update, group_and_project
        )

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "protect_branch_and_allowed_to_merge"
        )

        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]

        current_push_access_user_ids = []
        current_push_access_user_ids.sort()

        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = [user_allowed_to_merge_id]
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project, "*_and_allowed_to_push"
        )

        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]

        current_push_access_user_ids = [
            user_allowed_to_push_id,
            user_allowed_to_merge_id,
            user_allowed_to_push_and_allowed_to_merge_id,
        ]
        current_push_access_user_ids.sort()

        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = []
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        mixed_config_with_allow_access_levels_with_user_ids = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch_and_allow_access_levels_with_user_ids:
                protected: true
                push_access_level: {AccessLevel.DEVELOPER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user_id: {user_allowed_to_push_id}
                  - user: {users[2]}
                allowed_to_merge:
                  - access_level: {AccessLevel.DEVELOPER.value} 
                  - user_id: {user_allowed_to_merge_id}
                  - user: {users[0]}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(
            mixed_config_with_allow_access_levels_with_user_ids, group_and_project
        )

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project,
            "protect_branch_and_allow_access_levels_with_user_ids",
        )

        assert push_access_levels == [
            AccessLevel.DEVELOPER.value,
            AccessLevel.MAINTAINER.value,
        ]
        assert merge_access_levels == [
            AccessLevel.DEVELOPER.value,
            AccessLevel.MAINTAINER.value,
        ]

        current_push_access_user_ids = [
            user_allowed_to_push_id,
            user_allowed_to_push_and_allowed_to_merge_id,
        ]
        current_push_access_user_ids.sort()

        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = [
            user_allowed_to_merge_id,
            user_allowed_to_push_id,
        ]
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test_protect_branch_with_old_api_next_update_with_new_api_and_unprotect(
        self, gitlab, group_and_project, branches
    ):

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
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
        ) = gitlab.get_only_branch_access_levels(group_and_project, "protect_branch")
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is False

    def test_protect_branch_with_new_api_next_update_with_old_api_and_unprotect(
        self, gitlab, group_and_project, branches
    ):

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
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
        ) = gitlab.get_only_branch_access_levels(group_and_project, "protect_branch")
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is False

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test_protect_branch_with_old_api_next_update_with_new_api_and_userid_and_unprotect(
        self,
        gitlab,
        group_and_project,
        branches,
        users,
        one_maintainer_and_two_developers,
    ):

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        user_allowed_to_push_id = gitlab.get_user_to_protect_branch(users[0])
        user_allowed_to_merge_id = gitlab.get_user_to_protect_branch(users[1])

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: true
                push_access_level: {AccessLevel.DEVELOPER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                allowed_to_push:
                   - access_level: {AccessLevel.MAINTAINER.value} 
                   - user_id: {user_allowed_to_push_id}
                   - user: {users[1]}
                allowed_to_merge:
                   - access_level: {AccessLevel.MAINTAINER.value} 
                   - user_id: {user_allowed_to_merge_id}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, "protect_branch")

        assert push_access_levels == [
            AccessLevel.DEVELOPER.value,
            AccessLevel.MAINTAINER.value,
        ]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]

        current_push_access_user_ids = [
            user_allowed_to_push_id,
            user_allowed_to_merge_id,
        ]
        current_push_access_user_ids.sort()
        assert push_access_user_ids == current_push_access_user_ids

        current_merge_access_user_ids = [user_allowed_to_merge_id]
        current_merge_access_user_ids.sort()
        assert merge_access_user_ids == current_merge_access_user_ids

        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is False

    def test_unprotect_when_the_rest_of_the_parameters_are_still_specified_old_api(
        self, gitlab, group_and_project, branches
    ):

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_unprotect_branch_with_old_api = f"""
        gitlab:
          api_version: 4

        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: false
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_unprotect_branch_with_old_api, group_and_project)

        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is False

    def test_unprotect_when_the_rest_of_the_parameters_are_still_specified_new_api(
        self, gitlab, group_and_project, branches
    ):

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
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
        ) = gitlab.get_only_branch_access_levels(group_and_project, "protect_branch")
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_unprotect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              protect_branch:
                protected: false
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_unprotect_branch_with_new_api, group_and_project)

        # old API
        branch = gitlab.get_branch(group_and_project, "protect_branch")
        assert branch["protected"] is False

        # new API
        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, "protect_branch")
        assert push_access_levels is None
        assert merge_access_levels is None
        assert push_access_user_ids is None
        assert merge_access_user_ids is None
        assert unprotect_access_level is None
