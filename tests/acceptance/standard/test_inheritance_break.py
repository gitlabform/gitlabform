from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    get_only_branch_access_levels,
)


class TestInheritanceBreak:
    def test__can_choose_not_to_inherit_branch_protections_from_parent_group(
        self,
        group,
        project,
        branch,
        other_branch,
    ):
        # project will be created in the group by the fixture in conftest.py
        # branches will be created on the project by the fixtures
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
            other_branch_push_access_level,
            other_branch_merge_access_level,
            _,
            _,
            other_branch_unprotect_access_level,
        ) = get_only_branch_access_levels(project, other_branch)
        assert other_branch_push_access_level == [AccessLevel.MAINTAINER.value]
        assert other_branch_merge_access_level == [AccessLevel.DEVELOPER.value]
        assert other_branch_unprotect_access_level is AccessLevel.MAINTAINER.value
