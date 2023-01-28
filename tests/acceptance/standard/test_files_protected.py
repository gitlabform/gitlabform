from tests.acceptance import run_gitlabform, DEFAULT_README


class TestFilesProtected:
    # this test should be in a separate class than other test files as it changes too
    # much for a reasonable setup and cleanup using fixtures
    def test__set_file_protected_branches(self, project, branch, other_branch):

        set_file_protected_branches = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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

        run_gitlabform(set_file_protected_branches, project.path_with_namespace)

        for some_branch in [
            "main",  # main branch is protected by default
            other_branch,
        ]:
            project_file = project.files.get(ref=some_branch, file_path="README.md")
            assert (
                project_file.decode().decode("utf-8")
                == "Content for protected branches only"
            )
            some_branch = project.branches.get(some_branch)
            assert some_branch.protected is True

        for some_branch in [branch]:
            project_file = project.files.get(ref=some_branch, file_path="README.md")
            assert project_file.decode().decode("utf-8") == DEFAULT_README
            some_branch = project.branches.get(some_branch)
            assert some_branch.protected is False
