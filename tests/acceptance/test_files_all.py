from tests.acceptance import run_gitlabform


class TestFilesAll:

    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__set_file_all_branches(
        self, gitlab, group_and_project, branch, other_branch
    ):
        set_file_all_branches = f"""
        projects_and_groups:
          {group_and_project}:
            branches:
              {branch}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
              {other_branch}:
                protected: false
            files:
              "README.md":
                overwrite: true
                branches: all
                content: "Content for all branches"
        """
        run_gitlabform(set_file_all_branches, group_and_project)

        for some_branch in [
            "main",
            branch,
            other_branch,
        ]:
            file_content = gitlab.get_file(group_and_project, some_branch, "README.md")
            assert file_content == "Content for all branches"

        # check that this branch remains unprotected
        for some_branch in [
            other_branch,
        ]:
            some_branch = gitlab.get_branch(group_and_project, some_branch)
            assert some_branch["protected"] is False
