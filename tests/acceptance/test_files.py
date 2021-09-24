import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform, DEFAULT_README


@pytest.fixture(scope="function")
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
        if branch.startswith("protected"):
            gitlab.branch_access_level(
                f"{group}/{project}",
                branch,
                {
                    "push_access_level": AccessLevel.MAINTAINER.value,
                    "merge_access_level": AccessLevel.MAINTAINER.value,
                    "unprotect_access_level": AccessLevel.MAINTAINER.value,
                },
            )

    def fin():
        for branch in branches:
            gitlab.delete_branch(f"{group}/{project}", branch)

        gitlab.set_file(
            f"{group}/{project}",
            "main",
            "README.md",
            DEFAULT_README,
            "Reset default content",
        )

        gitlab.branch_access_level(
            f"{group}/{project}",
            "main",
            {
                "push_access_level": AccessLevel.MAINTAINER.value,
                "merge_access_level": AccessLevel.MAINTAINER.value,
                "unprotect_access_level": AccessLevel.MAINTAINER.value,
            },
        )

    request.addfinalizer(fin)


class TestFiles:
    def test__set_file_specific_branch(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_specific_branch = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              main:
                protected: true
                developers_can_push: false
                developers_can_merge: true
            files:
              "README.md":
                overwrite: true
                branches:
                  - main
                content: "Content for main only"
                commit_message: "Preconfigured commit message"
        """

        run_gitlabform(set_file_specific_branch, group_and_project_name)

        commit = gitlab.get_last_commit(group_and_project_name, "main")
        assert commit["message"] == "Preconfigured commit message"

        file_content = gitlab.get_file(group_and_project_name, "main", "README.md")
        assert file_content == "Content for main only"

        other_branch_file_content = gitlab.get_file(
            group_and_project_name, "protected_branch1", "README.md"
        )
        assert other_branch_file_content == DEFAULT_README

        # check if main stays protected after the file update
        branch = gitlab.get_branch(group_and_project_name, "main")
        assert branch["protected"] is True

    def test__set_file_all_branches(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_all_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              main:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch1:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch2:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch3:
                protected: true
                developers_can_push: false
                developers_can_merge: true
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

        # check if these remain unprotected
        # (main branch is protected by default)
        for branch in [
            "regular_branch1",
            "regular_branch2",
        ]:
            branch = gitlab.get_branch(group_and_project_name, branch)
            assert branch["protected"] is False

    def test__set_file_protected_branches(self, gitlab, group, project, branches):
        group_and_project_name = f"{group}/{project}"

        set_file_protected_branches = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              main:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch1:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch2:
                protected: true
                developers_can_push: false
                developers_can_merge: true
              protected_branch3:
                protected: true
                developers_can_push: false
                developers_can_merge: true
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
                developers_can_push: true
                developers_can_merge: true
            files:
              "README.md":
                overwrite: true
                branches: protected
                content: "Content for protected branches only"
        """

        run_gitlabform(set_file_protected_branches, group_and_project_name)

        for branch in [
            "main",  # main branch is protected by default
            "protected_branch1",
            "protected_branch2",
            "protected_branch3",
        ]:
            file_content = gitlab.get_file(group_and_project_name, branch, "README.md")
            assert file_content == "Content for protected branches only"
            branch = gitlab.get_branch(group_and_project_name, branch)
            assert branch["protected"] is True

        for branch in ["regular_branch1", "regular_branch2"]:
            file_content = gitlab.get_file(group_and_project_name, branch, "README.md")
            assert file_content == DEFAULT_README
            branch = gitlab.get_branch(group_and_project_name, branch)
            assert branch["protected"] is False

    def test_set_file_protected_branches_new_api(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        test_config = f"""
        projects_and_groups:
          {group_and_project_name}:
            branches:
              main:
                protected: true
                push_access_level: {AccessLevel.MAINTAINER.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        
            files:
              anyfile1:
                overwrite: true
                branches:
                  - main
                skip_ci: true
                content: foobar
        """

        run_gitlabform(test_config, group_and_project_name)

        file_content = gitlab.get_file(group_and_project_name, "main", "anyfile1")
        assert file_content == "foobar"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project_name, "main")
        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

    def test_set_file_protected_branches_new_api_not_all_levels(
        self, gitlab, group, project, branches
    ):
        group_and_project_name = f"{group}/{project}"

        test_config = f"""
            projects_and_groups:
              {group_and_project_name}:
                branches:
                  regular_branch1:
                    protected: true
                    push_access_level: {AccessLevel.DEVELOPER.value}
                    merge_access_level: {AccessLevel.DEVELOPER.value}

                files:
                  anyfile2:
                    overwrite: true
                    branches:
                      - regular_branch1
                    content: barfoo
            """

        run_gitlabform(test_config, group_and_project_name)

        file_content = gitlab.get_file(
            group_and_project_name, "regular_branch1", "anyfile2"
        )
        assert file_content == "barfoo"

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(
            group_and_project_name, "regular_branch1"
        )
        assert push_access_levels == [AccessLevel.DEVELOPER.value]
        assert merge_access_levels == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        # the default value
        # according to https://docs.gitlab.com/ee/api/protected_branches.html#protect-repository-branches
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
