from tests.acceptance import run_gitlabform


class TestFilesAll:
    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__set_file_all_branches(self, project, branch, other_branch):
        set_file_all_branches = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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
        run_gitlabform(set_file_all_branches, project.path_with_namespace)

        for some_branch in [
            "main",
            branch,
            other_branch,
        ]:
            project_file = project.files.get(ref=some_branch, file_path="README.md")
            assert project_file.decode().decode("utf-8") == "Content for all branches"

        # check that this branch remains unprotected
        for some_branch in [
            other_branch,
        ]:
            some_branch = project.branches.get(some_branch)
            assert some_branch.protected is False
