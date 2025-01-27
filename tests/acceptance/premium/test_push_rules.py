import pytest
from tests.acceptance import run_gitlabform

pytestmark = pytest.mark.requires_license


class TestPushRules:
    def test__create_push_rules(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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

        run_gitlabform(config, project)

        push_rules = project.pushrules.get()
        assert push_rules.max_file_size == 0

    def test__edit_push_rules(self, project):
        self.test__create_push_rules(project)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
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

        run_gitlabform(config, project)

        push_rules = project.pushrules.get()
        assert push_rules.max_file_size == 2

    def test__changing_author_email_regex(self, project):
        initial_regex = (
            "\@(?:(?:engineering\.digital\.)?co\.uk|(?:users\.)?noreply\.gitlab\.com)$"
        )
        initial_config = f"""
                projects_and_groups:
                  {project.path_with_namespace}:
                    project_push_rules:
                      commit_message_regex: 'Fixes \\d +'
                      branch_name_regex: ""
                      deny_delete_tag: false
                      member_check: false
                      prevent_secrets: false
                      author_email_regex: {initial_regex}
                      file_name_regex: ""
                """

        run_gitlabform(initial_config, project)

        initial_push_rules = project.pushrules.get()
        assert initial_push_rules.author_email_regex == initial_regex

        updated_regex = "\@(?:(?:engineering\.digital\.)?co\.uk|(?:users\.)?noreply\.gitlab-dedicated\.com)$"
        updated_config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_push_rules:
              commit_message_regex: 'Fixes \\d +'
              branch_name_regex: ""
              deny_delete_tag: false
              member_check: false
              prevent_secrets: false
              author_email_regex: {updated_regex}
              file_name_regex: ""
              max_file_size: 2 # in MB, 0 means unlimited
        """

        run_gitlabform(updated_config, project)

        push_rules = project.pushrules.get()
        assert push_rules.author_email_regex == updated_regex
