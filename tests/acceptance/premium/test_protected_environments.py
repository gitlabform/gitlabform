from unittest import TestCase

import pytest
from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform, gl


class TestProtectedEnvironments(TestCase):
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__protect_a_repository_environment(
        self, gitlab, group_and_project, make_user
    ):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {group_and_project}:
            protected_environments:
              enforce: true
              foo:
                name: foo
                deploy_access_levels:
                  - access_level: 40
                    group_inheritance_type: 0
                  - user_id: {user1.id}
                  - user: {user2.name}
        """

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0]["name"] == "foo"
        assert len(protected_envs_under_this_project[0]["deploy_access_levels"]) == 3

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__unprotect_environment(self, gitlab, group_and_project, make_user):
        self.test__protect_a_repository_environment(
            gitlab, group_and_project, make_user
        )

        config = f"""
        projects_and_groups:
          {group_and_project}:
            protected_environments:
              enforce: true
        """

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 0
