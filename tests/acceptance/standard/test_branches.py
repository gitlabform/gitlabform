from gitlabform.gitlab import AccessLevel
from tests.acceptance import get_only_branch_access_levels, run_gitlabform


class TestBranches:
    def test__protect_and_unprotect(self, project, branch):
        config_protect_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_protect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels == [AccessLevel.NO_ACCESS.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value

        config_unprotect_branch = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: false
                push_access_level: {AccessLevel.NO_ACCESS.value}
                merge_access_level: {AccessLevel.MAINTAINER.value}
                unprotect_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_unprotect_branch, project.path_with_namespace)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_levels is None
        assert merge_access_levels is None
        assert push_access_user_ids is None
        assert merge_access_user_ids is None
        assert unprotect_access_level is None

    def test__config_with_access_level_names(self, project, branch):
        config_with_access_levels_names = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                push_access_level: no_access        # note "_" or " " and the various
                merge_access_level: Developer       # case in each line. it should not
                unprotect_access_level: MAINTAINER  # matter as we allow any case.
        """

        run_gitlabform(config_with_access_levels_names, project.path_with_namespace)

        (
            push_access_level,
            merge_access_level,
            push_access_user_ids,
            merge_access_user_ids,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_level == [AccessLevel.NO_ACCESS.value]
        assert merge_access_level == [AccessLevel.DEVELOPER.value]
        assert push_access_user_ids == []
        assert merge_access_user_ids == []
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
