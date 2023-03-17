from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    get_only_branch_access_levels,
)


class TestInheritanceBreak:
    def test__inheritance_break(
        self,
        group,
        project,
        branch,
        other_branch,
    ):
        config_yaml = f"""
        projects_and_groups:
          {group.full_path}/*:
            branches:   
              {branch}:
                protected: true
                push_access_level: developer
                merge_access_level: developer
                unprotect_access_level: maintainer
              
          {project.path_with_namespace}:
            branches:
              inherit: false
              {other_branch}:
                protected: true
                push_access_level: maintainer
                merge_access_level: developer
                unprotect_access_level: maintainer
        """

        run_gitlabform(config_yaml, project.path_with_namespace)

        (
            push_access_level,
            merge_access_level,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, branch)
        assert push_access_level is None
        assert merge_access_level is None
        assert unprotect_access_level is None

        (
            push_access_level,
            merge_access_level,
            _,
            _,
            unprotect_access_level,
        ) = get_only_branch_access_levels(project, other_branch)
        assert push_access_level == [AccessLevel.MAINTAINER.value]
        assert merge_access_level == [AccessLevel.DEVELOPER.value]
        assert unprotect_access_level is AccessLevel.MAINTAINER.value
