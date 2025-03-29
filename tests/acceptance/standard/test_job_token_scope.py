import logging
from gitlab.v4.objects import Project, Group

from tests.acceptance import (
    run_gitlabform,
)


class TestProjectJobTokenScope:
    def test__enable_limit_access_to_this_project(
        self,
        project: Project,
    ):
        self._setup_limit_access_state(project, False)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # inbound_enabled is what GL returns from GET
        # https://docs.gitlab.com/ee/api/project_job_token_scopes.html#get-a-projects-cicd-job-token-access-settings
        # to denote whether "Limit Access to this Project" is enabled or not
        assert scope.inbound_enabled

    def test__disable_limit_access_to_this_project(
        self,
        project: Project,
    ):
        self._setup_limit_access_state(project, True)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: false
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # inbound_enabled is what GL returns from GET
        # https://docs.gitlab.com/ee/api/project_job_token_scopes.html#get-a-projects-cicd-job-token-access-settings
        # to denote whether "Limit Access to this Project" is enabled or not
        assert not scope.inbound_enabled

    def test__add_other_project_to_job_token_scope_by_name(
        self,
        project: Project,
        other_project: Project,
        message_recorder,
    ):
        self._restore_default_allowlist_state(project)

        # By default allowlist for a project always contains itself
        assert len(project.job_token_scope.get().allowlist.list()) == 1

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                enforce: true
                projects:
                  - {other_project.path_with_namespace}
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        allowlist_after = scope.allowlist.list()

        # Validate other_project added to allowlist
        assert len(allowlist_after) == 2
        assert any(allowed.id == other_project.id for allowed in allowlist_after)

        # Validate nothing on groups_allowlist
        assert len(scope.groups_allowlist.list()) == 0

        assert message_recorder.find(f"Added Project {other_project.get_id()} to allowlist")

    def test__adding_project_already_on_allowlist_via_config(
        self,
        project: Project,
        other_project: Project,
        message_recorder,
    ):
        self._restore_default_allowlist_state(project)

        job_token_scope = project.job_token_scope.get()
        job_token_scope.allowlist.create({"target_project_id": other_project.get_id()})
        job_token_scope.save()

        # By default allowlist for a project always contains itself
        assert len(job_token_scope.allowlist.list()) == 2
        assert len(job_token_scope.groups_allowlist.list()) == 0

        job_token_scope_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                enforce: true
                projects:
                  - {other_project.path_with_namespace}
        """

        run_gitlabform(job_token_scope_config, project)

        scope = project.job_token_scope.get()

        allowlist_after = scope.allowlist.list()

        # Validate other_project added to allowlist
        assert len(allowlist_after) == 2
        assert any(allowed.id == other_project.id for allowed in allowlist_after)

        # Validate nothing on groups_allowlist
        assert len(scope.groups_allowlist.list()) == 0

        assert message_recorder.find(f"Added Project {other_project.get_id()} to allowlist") is None

    def test__add_other_project_to_job_token_scope_by_id(
        self,
        project: Project,
        other_project: Project,
    ):
        self._restore_default_allowlist_state(project)

        # By default allowlist for a project always contains itself
        assert len(project.job_token_scope.get().allowlist.list()) == 1

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                projects:
                  - {other_project.id}
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        allowlist_after = scope.allowlist.list()

        # Validate other_project added to allowlist
        assert len(allowlist_after) == 2
        assert any(allowed.id == other_project.id for allowed in allowlist_after)

        # Validate nothing on groups_allowlist
        assert len(scope.groups_allowlist.list()) == 0

    def test__existing_projects_and_groups_removed_from_allowlists_when_no_allowlist_provided_in_config(
        self,
        project: Project,
        other_project: Project,
        other_group: Group,
    ):
        self._restore_default_allowlist_state(project)

        self._setup_add_other_project_to_allowlist(other_project, project)
        self._setup_add_other_group_to_allowlist(other_group, project)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                enforce: true
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # Validate other_project no longer on allowlist
        projects_allowlist_after = scope.allowlist.list()
        assert len(projects_allowlist_after) == 1
        assert not any(allowed.id == other_project.id for allowed in projects_allowlist_after)

        # Validate nothing on groups_allowlist
        assert len(scope.groups_allowlist.list()) == 0

    def test__existing_projects_and_groups_removed_from_allowlists_when_no_allowlist_provided_in_config_and_limit_access_to_this_project_set_to_false(
        self,
        project: Project,
        other_project: Project,
        other_group: Group,
    ):
        self._restore_default_allowlist_state(project)

        # Limit access and add project + group to allowlist
        scope = project.job_token_scope.get()
        scope.enabled = True
        scope.save()

        self._setup_add_other_project_to_allowlist(other_project, project)
        self._setup_add_other_group_to_allowlist(other_group, project)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: false
              allowlist:
                enforce: true
        """

        run_gitlabform(job_token_scope, project)

        updated_scope = project.job_token_scope.get()

        # Validate other_project no longer on allowlist
        projects_allowlist_after = updated_scope.allowlist.list()
        assert len(projects_allowlist_after) == 1
        assert not any(allowed.id == other_project.id for allowed in projects_allowlist_after)

        # Validate nothing on groups_allowlist
        assert len(updated_scope.groups_allowlist.list()) == 0

    def test__existing_projects_not_removed_from_allowlist_when_enforce_is_not_set_and_when_only_group_specified_in_config(
        self,
        project: Project,
        other_project: Project,
        other_group: Group,
    ):
        self._restore_default_allowlist_state(project)

        self._setup_add_other_project_to_allowlist(other_project, project)

        job_token_scope = f"""
           projects_and_groups:
             {project.path_with_namespace}:
               job_token_scope:
                 limit_access_to_this_project: true
                 allowlist:
                   groups:
                     - {other_group.id}
           """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # Validate other_project still on allowlist
        projects_allowlist_after = scope.allowlist.list()
        assert len(projects_allowlist_after) == 2

        assert any(allowed.id == other_project.id for allowed in projects_allowlist_after)

        # Validate other_group added to allowlist
        groups_allowlist_after = scope.groups_allowlist.list()
        assert len(groups_allowlist_after) == 1

        assert any(allowed.id == other_group.id for allowed in groups_allowlist_after)

    def test__existing_projects_removed_from_allowlist_when_enforce_is_true_and_when_only_group_specified_in_config(
        self,
        project: Project,
        other_project: Project,
        other_group: Group,
    ):
        self._restore_default_allowlist_state(project)

        self._setup_add_other_project_to_allowlist(other_project, project)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                enforce: true
                groups:
                  - {other_group.id}
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # Validate other_project no longer on allowlist
        projects_allowlist_after = scope.allowlist.list()
        assert len(projects_allowlist_after) == 1

        assert not any(allowed.id == other_project.id for allowed in projects_allowlist_after)

        # Validate other_group added to allowlist
        groups_allowlist_after = scope.groups_allowlist.list()
        assert len(groups_allowlist_after) == 1

        assert any(allowed.id == other_group.id for allowed in groups_allowlist_after)

    def test__add_group_to_job_token_scope_by_name(
        self,
        project: Project,
        other_group: Group,
        message_recorder,
    ):
        self._restore_default_allowlist_state(project)

        job_token_scope = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            job_token_scope:
              limit_access_to_this_project: true
              allowlist:
                groups:
                  - {other_group.name}
        """

        run_gitlabform(job_token_scope, project)

        scope = project.job_token_scope.get()

        # Validate other_group added to allowlist
        groups_allowlist_after = scope.groups_allowlist.list()
        assert len(groups_allowlist_after) == 1

        assert any(allowed.id == other_group.id for allowed in groups_allowlist_after)

        assert message_recorder.find(f"Added Group {other_group.get_id()} to allowlist")

    def test__adding_group_already_on_allowlist_via_config(
        self,
        project: Project,
        other_group: Group,
        message_recorder,
    ):
        self._restore_default_allowlist_state(project)

        job_token_scope = project.job_token_scope.get()
        job_token_scope.groups_allowlist.create({"target_group_id": other_group.get_id()})
        job_token_scope.save()

        job_token_scope_config = f"""
           projects_and_groups:
             {project.path_with_namespace}:
               job_token_scope:
                 limit_access_to_this_project: true
                 allowlist:
                   groups:
                     - {other_group.name}
           """

        run_gitlabform(job_token_scope_config, project)

        scope = project.job_token_scope.get()

        # Validate other_group added to allowlist
        groups_allowlist_after = scope.groups_allowlist.list()
        assert len(groups_allowlist_after) == 1

        assert any(allowed.id == other_group.id for allowed in groups_allowlist_after)

        assert message_recorder.find(f"Added Group {other_group.get_id()} to allowlist") is None

    @staticmethod
    def _setup_limit_access_state(project: Project, state: bool):
        scope = project.job_token_scope.get()
        scope.enabled = state
        scope.save()

    @staticmethod
    def _setup_add_other_project_to_allowlist(other_project: Project, project: Project):
        job_token_scope = project.job_token_scope.get()
        job_token_scope.allowlist.create({"target_project_id": other_project.id})

    @staticmethod
    def _setup_add_other_group_to_allowlist(other_group: Group, project: Project):
        job_token_scope = project.job_token_scope.get()
        job_token_scope.groups_allowlist.create({"target_group_id": other_group.id})

    @staticmethod
    def _restore_default_allowlist_state(project: Project):
        job_token_scope = project.job_token_scope.get()

        for other_proj in job_token_scope.allowlist.list():
            project_id = other_proj.id
            if project_id != project.id:
                job_token_scope.allowlist.delete(project_id)

        for group in job_token_scope.groups_allowlist.list():
            job_token_scope.groups_allowlist.delete(group.id)

        job_token_scope.save()
