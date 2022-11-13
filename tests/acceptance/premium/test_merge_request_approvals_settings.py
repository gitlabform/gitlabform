import pytest

from tests.acceptance import run_gitlabform, gl


class TestMergeRequestApprovalsSettings:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__edit_settings(self, gitlab, group_and_project, make_user):

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              reset_approvals_on_push: false
              disable_overriding_approvers_per_merge_request: true
              merge_requests_author_approval: false
        """

        run_gitlabform(config, group_and_project)

        settings = gitlab.get_approvals_settings(group_and_project)

        assert settings["reset_approvals_on_push"] is False
        assert settings["disable_overriding_approvers_per_merge_request"] is True
        assert settings["merge_requests_author_approval"] is False

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              reset_approvals_on_push: true
              disable_overriding_approvers_per_merge_request: false
              merge_requests_author_approval: true
        """

        run_gitlabform(config, group_and_project)

        settings = gitlab.get_approvals_settings(group_and_project)

        assert settings["reset_approvals_on_push"] is True
        assert settings["disable_overriding_approvers_per_merge_request"] is False
        assert settings["merge_requests_author_approval"] is True

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__fail(self, gitlab, group_and_project, make_user):

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests_approvals:
              approvals_before_merge: 1
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, group_and_project)
