import pytest

from gitlabform.gitlab.core import NotFoundException
from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
    randomize_case,
)

pytestmark = pytest.mark.requires_license


class TestBranchesUsersCaseInsensitive:
    def test__users_case_insensitive(
        self,
        project,
        branch,
        make_user,
    ):
        first_user = make_user(AccessLevel.DEVELOPER)
        second_user = make_user(AccessLevel.DEVELOPER)
        third_user = make_user(AccessLevel.DEVELOPER)

        config_with_more_user_ids = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            branches:
              {branch}:
                protected: true
                allowed_to_push:
                  - access_level: {AccessLevel.MAINTAINER.value} 
                  - user: {randomize_case(first_user.username)}
                  - user: {randomize_case(second_user.username)}
                  - user: {randomize_case(third_user.username)}
                allowed_to_merge:
                  - access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config_with_more_user_ids, project)

        (
            push_access_levels,
            merge_access_levels,
            push_access_user_ids,
            merge_access_user_ids,
            _,
        ) = get_only_branch_access_levels(project, branch)

        assert push_access_levels == [AccessLevel.MAINTAINER.value]
        assert merge_access_levels == [AccessLevel.MAINTAINER.value]
        assert push_access_user_ids == sorted(
            [
                first_user.id,
                second_user.id,
                third_user.id,
            ]
        )
        assert merge_access_user_ids == []
