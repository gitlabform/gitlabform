import os
import pytest

from gitlabform.gitlab import AccessLevel
from gitlabform.gitlab.core import NotFoundException
from tests.acceptance import run_gitlabform, DEFAULT_README


@pytest.fixture(scope="function")
def no_access_branch(request, gitlab, group_and_project):
    gitlab.create_branch(group_and_project, "no_access_branch", "main")
    gitlab.protect_branch(
        group_and_project,
        "no_access_branch",
        {
            "push_access_level": AccessLevel.NO_ACCESS.value,
            "merge_access_level": AccessLevel.NO_ACCESS.value,
            "unprotect_access_level": AccessLevel.MAINTAINER.value,
        },
    )

    def fin():
        gitlab.unprotect_branch(group_and_project, "no_access_branch")
        gitlab.delete_branch(group_and_project, "no_access_branch")

    request.addfinalizer(fin)


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
    def test__set_file_specific_branch(self, gitlab, group_and_project, branch):

        set_file_specific_branch = f"""
        projects_and_groups:
          {group_and_project}:
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

        run_gitlabform(set_file_specific_branch, group_and_project)

        commit = gitlab.get_last_commit(group_and_project, branch)
        assert all(
            [text in commit["message"] for text in ["Automated", "made by gitlabform"]]
        )

        file_content = gitlab.get_file(group_and_project, branch, "README.md")
        assert file_content == f"Content for {branch} only"

        other_branch_file_content = gitlab.get_file(
            group_and_project, "main", "README.md"
        )
        assert other_branch_file_content == DEFAULT_README

        # check if main stays protected after the file update
        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True

    def test__set_file_strongly_protected_branch(
        self, gitlab, group_and_project, no_access_branch
    ):

        set_file_specific_branch = f"""
            projects_and_groups:
              {group_and_project}:
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

        run_gitlabform(set_file_specific_branch, group_and_project)

        commit = gitlab.get_last_commit(group_and_project, "no_access_branch")
        assert commit["message"] == "Automated change made by gitlabform"

        file_content = gitlab.get_file(
            group_and_project, "no_access_branch", "README.md"
        )
        assert file_content == "Content for no_access_branch only"

        other_branch_file_content = gitlab.get_file(
            group_and_project, "main", "README.md"
        )
        assert other_branch_file_content == DEFAULT_README

        # check if no_access_branch stays protected after the file update
        branch = gitlab.get_branch(group_and_project, "no_access_branch")
        assert branch["protected"] is True

    def test__delete_file_specific_branch(self, gitlab, group_and_project, branch):

        set_file_specific_branch = f"""
            projects_and_groups:
              {group_and_project}:
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

        run_gitlabform(set_file_specific_branch, group_and_project)

        commit = gitlab.get_last_commit(group_and_project, branch)
        assert commit["message"] == "Automated delete made by gitlabform"

        with pytest.raises(NotFoundException):
            gitlab.get_file(group_and_project, branch, "README.md")

        # check if main stays protected after the file delete
        the_branch = gitlab.get_branch(group_and_project, branch)
        assert the_branch["protected"] is True

    def test__custom_commit_message(self, gitlab, group_and_project, branch):

        set_file_specific_branch = f"""
        projects_and_groups:
          {group_and_project}:
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

        run_gitlabform(set_file_specific_branch, group_and_project)

        commit = gitlab.get_last_commit(group_and_project, branch)
        assert commit["message"] == "Preconfigured commit message [skip ci]"

    def test__set_file_protected_branches(self, gitlab, group_and_project, branch):

        test_config = f"""
        projects_and_groups:
          {group_and_project}:
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

        run_gitlabform(test_config, group_and_project)

        file_content = gitlab.get_file(group_and_project, branch, "anyfile1")
        assert file_content == "foobar"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__set_file_protected_branches_not_all_levels(
        self, gitlab, group_and_project, branch
    ):

        test_config = f"""
            projects_and_groups:
              {group_and_project}:
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

        run_gitlabform(test_config, group_and_project)

        file_content = gitlab.get_file(group_and_project, branch, "anyfile2")
        assert file_content == "barfoo"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        # the default value
        # according to https://docs.gitlab.com/ee/api/protected_branches.html#protect-repository-branches
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test__set_file_with_chinese_characters(self, gitlab, group_and_project, branch):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                content: |
                    Hanzi (Traditional): 丕不丈丁
                    Hanzi (Simplified): 丏丅丙两
        """

        run_gitlabform(set_file_chinese_characters, group_and_project)

        file_content = gitlab.get_file(group_and_project, branch, "README.md")
        assert file_content == "Hanzi (Traditional): 丕不丈丁\nHanzi (Simplified): 丏丅丙两"

    def test__set_external_file_with_chinese_characters(
        self, gitlab, group_and_project, branch, file
    ):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                file: file.txt
        """

        run_gitlabform(set_file_chinese_characters, group_and_project)

        file_content = gitlab.get_file(group_and_project, branch, "README.md")
        assert file_content == "Hanzi (Simplified): 丏丅丙两\nHanzi (Traditional): 丕不丈丁"

    def test__set_external_file_with_utf8_characters(
        self, gitlab, group_and_project, branch, file2
    ):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches:
                  - {branch}
                file: file2.txt
        """

        run_gitlabform(set_file_chinese_characters, group_and_project)

        file_content = gitlab.get_file(group_and_project, branch, "README.md")
        assert file_content == "LICENSE\n\n“This is a license file”"
