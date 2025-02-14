import os
import pytest
import time

from gitlab import GitlabGetError

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    get_only_branch_access_levels,
    run_gitlabform,
    DEFAULT_README,
)


@pytest.fixture(scope="function")
def no_access_branch(project):
    branch = project.branches.create({"branch": "no_access_branch", "ref": "main"})
    protected_branch = project.protectedbranches.create(
        {
            "name": "no_access_branch",
            "push_access_level": AccessLevel.NO_ACCESS.value,
            "merge_access_level": AccessLevel.NO_ACCESS.value,
            "unprotect_access_level": AccessLevel.MAINTAINER.value,
        },
    )

    yield branch

    protected_branch.delete()
    branch.delete()


@pytest.fixture(scope="class")
def file(request):
    f = open("file.txt", "a")
    f.write("Hanzi (Simplified): 丏丅丙两\nHanzi (Traditional): 丕不丈丁")
    f.close()

    def fin():
        os.remove("file.txt")

    request.addfinalizer(fin)


@pytest.fixture(scope="class")
def file2(request):
    f = open("file2.txt", "a")
    f.write("LICENSE\n\n“This is a license file”\n")
    f.close()

    def fin():
        os.remove("file2.txt")

    request.addfinalizer(fin)


class TestFiles:
    def test__set_file_specific_branch(self, project, branch):
        set_file_specific_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                content: "Content for {branch} only"
        """

        run_gitlabform(set_file_specific_branch, project.path_with_namespace)

        the_branch = project.branches.get(branch)
        assert all(
            [
                text in the_branch.commit["message"]
                for text in ["Automated", "made by gitlabform"]
            ]
        )

        project_file = project.files.get(ref=branch, file_path="README.md")
        assert project_file.decode().decode("utf-8") == f"Content for {branch} only"

        project_file = project.files.get(ref="main", file_path="README.md")
        assert project_file.decode().decode("utf-8") == DEFAULT_README

        # check if main stays protected after the file update
        assert the_branch.protected is True

    def test__does_not_commit_file_if_content_matches(self, project_for_function):
        set_file_specific_branch = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              main:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
            files:
              "README.md":
                overwrite: true
                branches:
                  - main
                content: {DEFAULT_README}
        """

        run_gitlabform(
            set_file_specific_branch, project_for_function.path_with_namespace
        )

        the_branch = project_for_function.branches.get("main")
        assert not any(
            [
                text in the_branch.commit["message"]
                for text in ["Automated", "made by gitlabform"]
            ]
        )

        project_file = project_for_function.files.get(ref="main", file_path="README.md")
        assert project_file.decode().decode("utf-8") == DEFAULT_README

        # check if main stays protected after the file update
        assert the_branch.protected is True

    def test__set_file_strongly_protected_branch(self, project, no_access_branch):
        set_file_specific_branch = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  no_access_branch:
                    protected: true
                    push_access_level: no access
                    merge_access_level: no access
                    unprotect_access_level: maintainer
                files:
                  "README.md":
                    overwrite: true
                    branches:
                      - no_access_branch
                    content: "Content for no_access_branch only"
            """

        run_gitlabform(set_file_specific_branch, project)

        branch = project.branches.get(no_access_branch.name)
        assert branch.commit["message"] == "Automated change made by gitlabform"

        project_file = project.files.get(ref="no_access_branch", file_path="README.md")
        assert (
            project_file.decode().decode("utf-8") == "Content for no_access_branch only"
        )

        project_file = project.files.get(ref="main", file_path="README.md")
        assert project_file.decode().decode("utf-8") == DEFAULT_README

        # Retry mechanism to check if no_access_branch stays protected after the file update
        for _ in range(5):
            branch = project.branches.get(no_access_branch.name)
            if branch.protected:
                break
            time.sleep(2)
        assert branch.protected is True

    def test__delete_file_protected_branch(self, project, branch):
        set_file_specific_branch = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  {branch}:
                    protected: true
                    push_access_level: maintainer
                    merge_access_level: developer
                    unprotect_access_level: maintainer
                files:
                  "README.md":
                    branches:
                      - {branch}
                    delete: true
            """

        run_gitlabform(set_file_specific_branch, project)

        the_branch = project.branches.get(branch)
        assert the_branch.commit["message"] == "Automated delete made by gitlabform"

        with pytest.raises(GitlabGetError):
            project.files.get(ref=branch, file_path="README.md")

        # check if main stays protected after the file delete
        the_branch = project.branches.get(the_branch.name)
        assert the_branch.protected is True

    def test__delete_file_unprotected_branch(
        self, project_for_function, branch_for_function
    ):
        set_file_specific_branch = f"""
            projects_and_groups:
              {project_for_function.path_with_namespace}:
                files:
                  "README.md":
                    branches:
                      - {branch_for_function}
                    delete: true
            """

        run_gitlabform(set_file_specific_branch, project_for_function)

        the_branch = project_for_function.branches.get(branch_for_function)
        assert the_branch.commit["message"] == "Automated delete made by gitlabform"

    def test__custom_commit_message(self, project, branch):
        set_file_specific_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: false
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                skip_ci: true
                content: "Hello world!"
                commit_message: "Preconfigured commit message"
        """

        run_gitlabform(set_file_specific_branch, project)

        branch = project.branches.get(branch)
        assert branch.commit["message"] == "Preconfigured commit message [skip ci]"

    def test__set_file_single_protected_branch(self, project, branch):
        test_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.MAINTAINER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
            files:
              anyfile1:
                overwrite: true
                branches:
                  - {branch}
                skip_ci: true
                content: foobar
        """

        run_gitlabform(test_config, project.path_with_namespace)

        project_file = project.files.get(ref=branch, file_path="anyfile1")
        assert project_file.decode().decode("utf-8") == "foobar"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__set_file_single_protected_branch_not_all_levels(self, project, branch):
        test_config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  {branch}:
                    protected: true
                    # use a level that will require unprotecting the branch
                    # to change the file value
                    push_access_level: {AccessLevel.MAINTAINER.value}
                    merge_access_level: {AccessLevel.MAINTAINER.value}
                files:
                  anyfile2:
                    overwrite: true
                    branches:
                      - {branch}
                    content: barfoo
            """

        run_gitlabform(test_config, project.path_with_namespace)

        project_file = project.files.get(ref=branch, file_path="anyfile2")
        assert project_file.decode().decode("utf-8") == "barfoo"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        # the default value
        # according to https://docs.gitlab.com/ee/api/protected_branches.html#protect-repository-branches
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__set_file_with_chinese_characters(self, project, branch):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                content: |
                    Hanzi (Traditional): 丕不丈丁
                    Hanzi (Simplified): 丏丅丙两
        """

        run_gitlabform(set_file_chinese_characters, project)

        file_content = project.files.get(ref=branch, file_path="README.md")
        assert (
            file_content.decode().decode("utf-8")
            == "Hanzi (Traditional): 丕不丈丁\nHanzi (Simplified): 丏丅丙两\n"
        )

    def test__set_external_file_with_chinese_characters(self, project, branch, file):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                file: file.txt
        """

        run_gitlabform(set_file_chinese_characters, project.path_with_namespace)

        project_file = project.files.get(ref=branch, file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == "Hanzi (Simplified): 丏丅丙两\nHanzi (Traditional): 丕不丈丁"
        )

    def test__set_external_file_with_utf8_characters(self, project, branch, file2):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                file: file2.txt
        """

        run_gitlabform(set_file_chinese_characters, project.path_with_namespace)

        project_file = project.files.get(ref=branch, file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == "LICENSE\n\n“This is a license file”\n"
        )

    def test__set_README_file_content_on_all_protected_branches(
        self, project_for_function, branch_for_function, other_branch_for_function
    ):
        set_file_protected_branches = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              main:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
              {branch_for_function}:
                protected: false
              {other_branch_for_function}:
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

        run_gitlabform(
            set_file_protected_branches, project_for_function.path_with_namespace
        )

        for some_branch in [
            "main",  # main branch is protected by default
            other_branch_for_function,
        ]:
            project_file = project_for_function.files.get(
                ref=some_branch, file_path="README.md"
            )
            assert (
                project_file.decode().decode("utf-8")
                == "Content for protected branches only"
            )
            some_branch = project_for_function.branches.get(some_branch)
            assert some_branch.protected is True

        project_file = project_for_function.files.get(
            ref=branch_for_function, file_path="README.md"
        )
        assert project_file.decode().decode("utf-8") == DEFAULT_README
        some_branch = project_for_function.branches.get(branch_for_function)
        assert some_branch.protected is False

    def test__set_README_file_content_on_all_branches(
        self, project_for_function, branch_for_function, other_branch_for_function
    ):
        set_file_all_branches = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}:
            branches:
              {branch_for_function}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
              {other_branch_for_function}:
                protected: false
            files:
              "README.md":
                overwrite: true
                branches: all
                content: "Content for all branches"
        """
        run_gitlabform(set_file_all_branches, project_for_function.path_with_namespace)

        for some_branch in [
            "main",
            branch_for_function,
            other_branch_for_function,
        ]:
            project_file = project_for_function.files.get(
                ref=some_branch, file_path="README.md"
            )
            assert project_file.decode().decode("utf-8") == "Content for all branches"

        # check that this branch remains unprotected
        other_branch = project_for_function.branches.get(other_branch_for_function)
        assert other_branch.protected is False
