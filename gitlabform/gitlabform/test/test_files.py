import pytest

from gitlabform.gitlabform.test import run_gitlabform


@pytest.fixture(scope="class")
def branches(request, gitlab, group, project):
    branches = [
        "protected_branch1",
        "protected_branch2",
        "protected_branch3",
        "regular_branch1",
        "regular_branch2",
    ]
    for branch in branches:
        gitlab.create_branch(f"{group}/{project}", branch, "main")

    def fin():
        pass
        # this will be deleted together with the project

    request.addfinalizer(fin)


class TestFiles:
    def test__set_file_specific_branch(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_specific_branch = f"""
        projects_and_groups:
          {group_and_project_name}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - main
                content: "Content for main only"
        """

        run_gitlabform(set_file_specific_branch, group_and_project_name)

        file_content = gitlab.get_file(group_and_project_name, "main", "README.md")
        assert file_content == "Content for main only"

        other_branch_file_content = gitlab.get_file(
            group_and_project_name, "protected_branch1", "README.md"
        )
        assert other_branch_file_content == "Hello World!"

    def test__set_file_all_branches(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_all_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            files:
              "README.md":
                overwrite: true
                branches: all
                content: "Content for all branches"
        """
        run_gitlabform(set_file_all_branches, group_and_project_name)

        for branch in [
            "main",
            "protected_branch1",
            "protected_branch2",
            "protected_branch3",
            "regular_branch1",
            "regular_branch2",
        ]:
            file_content = gitlab.get_file(group_and_project_name, branch, "README.md")
            assert file_content == "Content for all branches"

    def test__set_file_protected_branches(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_protected_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              protected_branch1:
                protected: true
                developers_can_push: true
                developers_can_merge: true
              protected_branch2:
                protected: true
                developers_can_push: true
                developers_can_merge: true
              protected_branch3:
                protected: true
                push_access_level: 30
                merge_access_level: 30
                unprotect_access_level: 40
            files:
              "README.md":
                overwrite: true
                branches: protected
                content: "Content for protected branches only"
        """

        run_gitlabform(set_file_protected_branches, group_and_project_name)

        # main branch is protected by default
        for branch in [
            "main",
            "protected_branch1",
            "protected_branch2",
            "protected_branch3",
        ]:
            file_content = gitlab.get_file(group_and_project_name, branch, "README.md")
            assert file_content == "Content for protected branches only"

        for branch in ["regular_branch1", "regular_branch2"]:
            file_content = gitlab.get_file(group_and_project_name, branch, "README.md")
            assert not file_content == "Content for protected branches only"

        branch = gitlab.get_branch_access_levels(
            group_and_project_name, "protected_branch3"
        )
        assert branch["push_access_levels"][0]["access_level"] is 30
        assert branch["merge_access_levels"][0]["access_level"] is 30
        assert branch["unprotect_access_levels"][0]["access_level"] is 40

    def test_unprotect_branch_new_api_bug(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        test_config = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              main:
                protected: true
                push_access_level: 40
                merge_access_level: 40
                unprotect_access_level: 40
        
            files:
              ".gitlab/merge_request_templates/MR.md":
                overwrite: true
                branches:
                  - main
                skip_ci: true
                content: foobar
        """

        run_gitlabform(test_config, group_and_project_name)

        file_content = gitlab.get_file(
            group_and_project_name, "main", ".gitlab/merge_request_templates/MR.md"
        )
        assert file_content == "foobar"

        branch = gitlab.get_branch_access_levels(group_and_project_name, "main")
        assert branch["push_access_levels"][0]["access_level"] is 40
        assert branch["merge_access_levels"][0]["access_level"] is 40
        assert branch["unprotect_access_levels"][0]["access_level"] is 40
