import pytest
from tests.acceptance import (
    run_gitlabform,
    get_gitlab,
)


gl = get_gitlab()


class TestPushRules:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__create_push_rules(self, gitlab, group, project):
        group_and_project = f"{group}/{project}"

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_push_rules:
              commit_message_regex: 'Fixes \\d +'
              branch_name_regex: ""
              deny_delete_tag: false
              member_check: false
              prevent_secrets: false
              author_email_regex: ""
              file_name_regex: ""
              max_file_size: 0 # in MB, 0 means unlimited
        """

        run_gitlabform(config, group_and_project)

        push_rules = gitlab.get_project_push_rules(group_and_project)
        assert push_rules["max_file_size"] == 0

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__edit_push_rules(self, gitlab, group, project):

        self.test__create_push_rules(gitlab, group, project)

        group_and_project = f"{group}/{project}"

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_push_rules:
              commit_message_regex: 'Fixes \\d +'
              branch_name_regex: ""
              deny_delete_tag: false
              member_check: false
              prevent_secrets: false
              author_email_regex: ""
              file_name_regex: ""
              max_file_size: 2 # in MB, 0 means unlimited
        """

        run_gitlabform(config, group_and_project)

        push_rules = gitlab.get_project_push_rules(group_and_project)
        assert push_rules["max_file_size"] == 2
