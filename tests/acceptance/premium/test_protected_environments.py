import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform, gl


class TestProtectedEnvironments:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__protect_a_repository_environment(
        self, gitlab, group_and_project, make_user
    ) -> str:

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
                  - user_id: {make_user(AccessLevel.DEVELOPER).id}
                  - user: {make_user(AccessLevel.DEVELOPER).name}
        """

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0]["name"] == "foo"
        assert len(protected_envs_under_this_project[0]["deploy_access_levels"]) == 3

        return config

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__add_user_to_protected_environment(
        self, gitlab, group_and_project, make_user
    ) -> str:
        config = self.test__protect_a_repository_environment(
            gitlab, group_and_project, make_user
        )

        config = f"""
        {config}
                  - user: {make_user(AccessLevel.DEVELOPER).name}
        """

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0]["name"] == "foo"
        assert len(protected_envs_under_this_project[0]["deploy_access_levels"]) == 4

        return config

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__remove_user_from_protected_environment(
        self, gitlab, group_and_project, make_user
    ) -> str:
        config = self.test__protect_a_repository_environment(
            gitlab, group_and_project, make_user
        )

        config = "\n".join(config.strip().split("\n")[:-1])

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0]["name"] == "foo"
        assert len(protected_envs_under_this_project[0]["deploy_access_levels"]) == 2

        return config

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__protect_a_second_repository_environment(
        self, gitlab, group_and_project, make_user
    ) -> str:
        user1 = make_user(AccessLevel.DEVELOPER)

        config = self.test__protect_a_repository_environment(
            gitlab, group_and_project, make_user
        )

        config = f"""
        {config}
              blah:
                name: blah
                deploy_access_levels:
                  - user: {user1.name}
        """

        run_gitlabform(config, group_and_project)

        protected_envs_under_this_project = gitlab.list_protected_environments(
            group_and_project
        )

        assert len(protected_envs_under_this_project) == 2
        blah_retrieved_info = [
            x for x in protected_envs_under_this_project if x["name"] == "blah"
        ]
        assert len(blah_retrieved_info) == 1
        assert len(blah_retrieved_info[0]["deploy_access_levels"]) == 1
        assert blah_retrieved_info[0]["deploy_access_levels"][0]["user_id"] == user1.id

        return config

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__unprotect_environment(self, gitlab, group_and_project, make_user):
        self.test__protect_a_second_repository_environment(
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
