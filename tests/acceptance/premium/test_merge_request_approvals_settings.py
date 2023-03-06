import pytest

from tests.acceptance import run_gitlabform, gl

pytestmark = pytest.mark.requires_license


class TestMergeRequestApprovalsSettings:
    def test__edit_settings(self, project, make_user):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              reset_approvals_on_push: false
              disable_overriding_approvers_per_merge_request: true
              merge_requests_author_approval: false
        """

        run_gitlabform(config, project)

        settings = project.approvals.get()

        assert settings.reset_approvals_on_push is False
        assert settings.disable_overriding_approvers_per_merge_request is True
        assert settings.merge_requests_author_approval is False

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              reset_approvals_on_push: true
              disable_overriding_approvers_per_merge_request: false
              merge_requests_author_approval: true
        """

        run_gitlabform(config, project)

        settings = project.approvals.get()

        assert settings.reset_approvals_on_push is True
        assert settings.disable_overriding_approvers_per_merge_request is False
        assert settings.merge_requests_author_approval is True

    def test__fail(self, project, make_user):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              approvals_before_merge: 1
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, project)
