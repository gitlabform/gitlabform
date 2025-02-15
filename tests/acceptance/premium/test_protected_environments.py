import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import run_gitlabform, get_only_environment_access_levels

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
        blah_retrieved_info = [x for x in protected_envs_under_this_project if x.name == "blah"]
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
        assert protected_envs_under_this_project[0].deploy_access_levels[0]["group_id"] == other_group.id

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
        assert protected_envs_under_this_project[0].deploy_access_levels[0]["group_id"] == other_group.id

    def test__environment_protection_dependent_on_members(self, project_for_function, group_for_function, make_user):
        """
        Configure an environment protection setting that depends on users or groups (i.e. allowed_to_deploy)
        Make sure the setting is applied successfully because users must be members
        before they can be configured in environment protection setting.
        """

        user_for_group_to_share_project_with = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)
        project_user_allowed_to_deploy = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)
        project_user_allowed_to_approve = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)

        config_branch_protection = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {user_for_group_to_share_project_with.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
          {project_for_function.path_with_namespace}:
            members:
              users:
                {project_user_allowed_to_deploy.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
                {project_user_allowed_to_approve.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
              groups:
                {group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
            protected_environments:
              production:
                deploy_access_levels:
                  - access_level: {AccessLevel.MAINTAINER.value}
                  - user_id: {project_user_allowed_to_deploy.id}
                  - group_id: {group_for_function.id}
                approval_rules:
                  - access_level: {AccessLevel.DEVELOPER.value}
                    required_approvals: 2
                  - user_id: {project_user_allowed_to_approve.id}
                  - group_id: {group_for_function.id}
        """

        run_gitlabform(config_branch_protection, project_for_function)

        protected_envs_under_this_project = project_for_function.protected_environments.list()
        assert len(protected_envs_under_this_project) == 1
        production_env_protection_details = protected_envs_under_this_project[0]
        assert production_env_protection_details.name == "production"
        assert len(production_env_protection_details.deploy_access_levels) == 3

        (
            deploy_access_levels,
            deploy_access_user_ids,
            deploy_access_group_ids,
            approval_rules_access_levels,
            approval_rules_user_ids,
            approval_rules_group_ids,
            _,
        ) = get_only_environment_access_levels(project_for_function, "production")

        assert deploy_access_levels == [AccessLevel.MAINTAINER.value]
        assert deploy_access_user_ids == sorted(
            [
                project_user_allowed_to_deploy.id,
            ]
        )
        assert deploy_access_group_ids == sorted(
            [
                group_for_function.id,
            ]
        )
        assert approval_rules_access_levels == [AccessLevel.DEVELOPER.value]
        assert approval_rules_user_ids == sorted(
            [
                project_user_allowed_to_approve.id,
            ]
        )
        assert approval_rules_group_ids == sorted([group_for_function.id])
