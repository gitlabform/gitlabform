from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    get_gitlab,
)


gl = get_gitlab()


class TestInheritanceBreak:
    def test__inheritance_break(
        self,
        gitlab,
        group,
        group_and_project,
        branch,
        other_branch,
    ):
        config_yaml = f"""
        projects_and_groups:
          {group}/*:
            branches:   
              {branch}:
                protected: true
                push_access_level: developer
                merge_access_level: developer
                unprotect_access_level: maintainer
              
          {group_and_project}:
            branches:
              inherit: false
              {other_branch}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
        """

        run_gitlabform(config_yaml, group_and_project)

        (
            push_access_level,
            merge_access_level,
            _,
            _,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, branch)
        assert push_access_level is None
        assert merge_access_level is None
        assert unprotect_access_level is None

        (
            push_access_level,
            merge_access_level,
            _,
            _,
            unprotect_access_level,
        ) = gitlab.get_only_branch_access_levels(group_and_project, other_branch)
        assert push_access_level == [AccessLevel.MAINTAINER.value]
        assert merge_access_level == [AccessLevel.DEVELOPER.value]
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
