import pytest

from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import (
    delete_group_and_project,
    run_gitlabform,
)


@pytest.fixture(scope="class")
def branches(request, gitlab, group, project):

    branches = [
        "protect_branch_but_allow_all",
        "protect_branch_with_code_owner_approval_required",
        "protect_branch_and_disallow_all",
        "protect_branch_and_allow_merges",
        "protect_branch_and_allow_pushes",
        "protect_branch_and_allow_merges_access_levels",
        "protect_branch_and_allow_pushes_access_levels",
        "protect_branch",
    ]
    for branch in branches:
        gitlab.create_branch(f"{group}/{project}", branch, "main")

    def fin():
        pass
        # this will be deleted together with the project

    request.addfinalizer(fin)


# protect_branch_with_code_owner_approval_required = f"""
# projects_and_groups:
#   {group_and_project_name}:
#     branches:
#       protect_branch_with_code_owner_approval_required:
#         protected: true
#         developers_can_push: false
#         developers_can_merge: true
#         code_owner_approval_required: true
# """


class TestBranches:
    def test__protect_branch_but_allow_all(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        protect_branch_but_allow_all = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_but_allow_all:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """
        run_gitlabform(protect_branch_but_allow_all, group_and_project_name)
        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_but_allow_all"
        )
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        # branch_access_levels = gitlab.get_branch_access_levels(
        #     group_and_project_name, "protect_branch_but_allow_all"
        # )
        # assert branch_access_levels["code_owner_approval_required"] is False

        # this test will pass only on GitLab EE
        # def test__protect_branch_with_code_owner_approval_required(self, gitlab):
        #     gf = GitLabForm(
        #         config_string=protect_branch_with_code_owner_approval_required,
        #         project_or_group=group_and_project_name,
        #     )
        #     gf.main()
        #
        #     branch_access_levels = gitlab.get_branch_access_levels(
        #         group_and_project_name, "protect_branch_with_code_owner_approval_required"
        #     )
        #     assert branch_access_levels["code_owner_approval_required"] is True

    def test__protect_branch_and_disallow_all(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        protect_branch_and_disallow_all = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_and_disallow_all:
                protected: true
                developers_can_push: false
                developers_can_merge: false
        """
        run_gitlabform(protect_branch_and_disallow_all, group_and_project_name)
        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_disallow_all"
        )
        assert branch["protected"] is True
        assert branch["developers_can_push"] is False
        assert branch["developers_can_merge"] is False

    def test__mixed_config(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        mixed_config = f"""
        projects_and_groups:
          {group_and_project_name}:
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
        run_gitlabform(mixed_config, group_and_project_name)
        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_merges"
        )
        assert branch["protected"] is True
        assert branch["developers_can_push"] is False
        assert branch["developers_can_merge"] is True

        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_pushes"
        )
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is False

        unprotect_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_and_allow_merges:
                protected: false
              protect_branch_and_allow_pushes:
                protected: false
        """
        run_gitlabform(unprotect_branches, group_and_project_name)

        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_merges"
        )
        assert branch["protected"] is False

        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_pushes"
        )
        assert branch["protected"] is False

    def test__mixed_config_with_new_api(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        mixed_config_with_access_levels = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: true
                push_access_level: 0
                merge_access_level: 30
                unprotect_access_level: 40
              '*_allow_pushes_access_levels':
                protected: true
                push_access_level: 30
                merge_access_level: 30
                unprotect_access_level: 40
        """

        run_gitlabform(mixed_config_with_access_levels, group_and_project_name)

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protect_branch_and_allow_merges_access_levels"
        )
        assert branch["push_access_levels"][0]["access_level"] is 0
        assert branch["merge_access_levels"][0]["access_level"] is 30
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "*_allow_pushes_access_levels"
        )
        assert branch["push_access_levels"][0]["access_level"] is 30
        assert branch["merge_access_levels"][0]["access_level"] is 30
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        mixed_config_with_access_levels_update = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: true
                push_access_level: 0
                merge_access_level: 40
                unprotect_access_level: 40
              '*_allow_pushes_access_levels':
                protected: true
                push_access_level: 40
                merge_access_level: 40
                unprotect_access_level: 40
        """

        run_gitlabform(mixed_config_with_access_levels_update, group_and_project_name)

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protect_branch_and_allow_merges_access_levels"
        )
        assert branch["push_access_levels"][0]["access_level"] is 0
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "*_allow_pushes_access_levels"
        )
        assert branch["push_access_levels"][0]["access_level"] is 40
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        mixed_config_with_access_levels_unprotect_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch_and_allow_merges_access_levels:
                protected: false
              '*_allow_pushes_access_levels':
                protected: false
        """

        run_gitlabform(
            mixed_config_with_access_levels_unprotect_branches, group_and_project_name
        )

        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_merges_access_levels"
        )
        assert branch["protected"] is False

        branch = gitlab.get_branch(
            group_and_project_name, "protect_branch_and_allow_pushes_access_levels"
        )
        assert branch["protected"] is False

    def test_protect_branch_with_old_api_next_update_with_new_api_and_unprotect(
        self, gitlab, group, project, branches
    ):
        group_and_project_name = f"{group}/{project}"

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                push_access_level: 0
                merge_access_level: 40
                unprotect_access_level: 40
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project_name)

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protect_branch"
        )
        assert branch["push_access_levels"][0]["access_level"] is 0
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is False

    def test_protect_branch_with_new_api_next_update_with_old_api_and_unprotect(
        self, gitlab, group, project, branches
    ):
        group_and_project_name = f"{group}/{project}"

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                push_access_level: 0
                merge_access_level: 40
                unprotect_access_level: 40
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project_name)

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protect_branch"
        )
        assert branch["push_access_levels"][0]["access_level"] is 0
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_protect_branch_unprotect = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: false
        """

        run_gitlabform(config_protect_branch_unprotect, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is False

    def test_unprotect_when_the_rest_of_the_parameters_are_still_specified_old_api(
        self, gitlab, group, project, branches
    ):
        group_and_project_name = f"{group}/{project}"

        config_protect_branch_with_old_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_protect_branch_with_old_api, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is True
        assert branch["developers_can_push"] is True
        assert branch["developers_can_merge"] is True

        config_unprotect_branch_with_old_api = f"""
        gitlab:
          api_version: 4
        
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: false
                developers_can_push: true
                developers_can_merge: true
        """

        run_gitlabform(config_unprotect_branch_with_old_api, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is False

    def test_unprotect_when_the_rest_of_the_parameters_are_still_specified_new_api(
        self, gitlab, group, project, branches
    ):
        group_and_project_name = f"{group}/{project}"

        config_protect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: true
                push_access_level: 0
                merge_access_level: 40
                unprotect_access_level: 40
        """

        run_gitlabform(config_protect_branch_with_new_api, group_and_project_name)

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protect_branch"
        )
        assert branch["push_access_levels"][0]["access_level"] is 0
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

        config_unprotect_branch_with_new_api = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protect_branch:
                protected: false
                push_access_level: 0
                merge_access_level: 40
                unprotect_access_level: 40
        """

        run_gitlabform(config_unprotect_branch_with_new_api, group_and_project_name)

        branch = gitlab.get_branch(group_and_project_name, "protect_branch")
        assert branch["protected"] is False
