from tests.acceptance import run_gitlabform, DEFAULT_README


class TestFilesProtected:
    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__set_file_protected_branches(
        self, gitlab, group_and_project, branch, other_branch
    ):
        set_file_protected_branches = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              main:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
              {branch}:
                protected: false
              {other_branch}:
                protected: true
                push_access_level: developer
                merge_access_level: developer
                unprotect_access_level: maintainer
            files:
              "README.md":
                overwrite: true
                branches: protected
                content: "Content for protected branches only"
        """

        run_gitlabform(set_file_protected_branches, group_and_project)

        for some_branch in [
            "main",  # main branch is protected by default
            other_branch,
        ]:
            file_content = gitlab.get_file(group_and_project, some_branch, "README.md")
            assert file_content == "Content for protected branches only"
            some_branch = gitlab.get_branch(group_and_project, some_branch)
            assert some_branch["protected"] is True

        for some_branch in [branch]:
            file_content = gitlab.get_file(group_and_project, some_branch, "README.md")
            assert file_content == DEFAULT_README
            some_branch = gitlab.get_branch(group_and_project, some_branch)
            assert some_branch["protected"] is False
