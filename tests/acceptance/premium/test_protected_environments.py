import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform, gl

pytestmark = pytest.mark.requires_license


class TestProtectedEnvironments:
    def test__protect_a_repository_environment(self, project, make_user) -> str:
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            protected_environments:
              enforce: true
              foo:
                deploy_access_levels:
                  - access_level: maintainer
                    group_inheritance_type: 0
                  - user_id: {make_user(AccessLevel.DEVELOPER).id}
                  - user: {make_user(AccessLevel.DEVELOPER).username}
        """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0].name == "foo"
        assert len(protected_envs_under_this_project[0].deploy_access_levels) == 3

        return config

    def test__add_user_to_protected_environment(self, project, make_user) -> str:
        config = self.test__protect_a_repository_environment(project, make_user)

        config = f"""
        {config}
                  - user: {make_user(AccessLevel.DEVELOPER).username}
        """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0].name == "foo"
        assert len(protected_envs_under_this_project[0].deploy_access_levels) == 4

        return config

    def test__remove_user_from_protected_environment(self, project, make_user) -> str:
        config = self.test__protect_a_repository_environment(project, make_user)

        config = "\n".join(config.strip().split("\n")[:-1])

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0].name == "foo"
        assert len(protected_envs_under_this_project[0].deploy_access_levels) == 2

        return config

    def test__protect_a_second_repository_environment(self, project, make_user) -> str:
        user1 = make_user(AccessLevel.DEVELOPER)

        config = self.test__protect_a_repository_environment(project, make_user)

        config = f"""
        {config}
              blah:
                deploy_access_levels:
                  - user: {user1.username}
        """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 2
        blah_retrieved_info = [
            x for x in protected_envs_under_this_project if x.name == "blah"
        ]
        assert len(blah_retrieved_info) == 1
        assert len(blah_retrieved_info[0].deploy_access_levels) == 1
        assert blah_retrieved_info[0].deploy_access_levels[0]["user_id"] == user1.id

        return config

    def test__unprotect_environment(self, project, make_user):
        self.test__protect_a_second_repository_environment(project, make_user)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            protected_environments:
              enforce: true
        """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 0

    def test__protect_a_repository_environment_group_name(self, project, other_group):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                members:
                  groups:
                    {other_group.full_path}:
                      group_access: {AccessLevel.MAINTAINER.value}
                protected_environments:
                  enforce: true
                  foo:
                    deploy_access_levels:
                      - group: {other_group.id}
            """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0].name == "foo"
        assert len(protected_envs_under_this_project[0].deploy_access_levels) == 1
        assert (
            protected_envs_under_this_project[0].deploy_access_levels[0]["group_id"]
            == other_group.id
        )

    def test__protect_a_repository_environment_group_id(self, project, other_group):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                members:
                  groups:
                    {other_group.full_path}:
                      group_access: {AccessLevel.MAINTAINER.value}
                protected_environments:
                  enforce: true
                  foo:
                    deploy_access_levels:
                      - group_id: {other_group.id}
            """

        run_gitlabform(config, project)

        protected_envs_under_this_project = project.protected_environments.list()

        assert len(protected_envs_under_this_project) == 1
        assert protected_envs_under_this_project[0].name == "foo"
        assert len(protected_envs_under_this_project[0].deploy_access_levels) == 1
        assert (
            protected_envs_under_this_project[0].deploy_access_levels[0]["group_id"]
            == other_group.id
        )
