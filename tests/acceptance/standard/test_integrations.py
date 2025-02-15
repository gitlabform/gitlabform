import pytest

from gitlab import GitlabGetError
from tests.acceptance import allowed_codes, run_gitlabform


@pytest.fixture(scope="function")
def integrations(project):
    integrations = ["asana", "slack", "redmine", "jira", "mattermost"]

    yield integrations

    # disable test integrations
    for integration in integrations:
        with allowed_codes(404):
            project.integrations.delete(integration)


class TestIntegrations:
    # we use "other_project" here on purpose because if we would reuse the "project"
    # then we could end up with running this test after another, and a integration created
    # and then deleted is a different entity in GitLab than a never created one (!).
    # the first one exists but has "active" field set to False, the other throws 404
    def test__if_they_are_not_set_by_default(self, other_project):
        for integration_name in ["asana", "slack", "redmine", "jira"]:
            with pytest.raises(GitlabGetError):
                other_project.integrations.get(integration_name)

    def test__if_delete_works(self, project):
        config_integrations = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: false
                commit_events: true
              asana:
                api_key: foo
                push_events: true
                active: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_integrations, project)

        for integration_name in ["jira", "asana", "slack"]:
            integration = project.integrations.get(integration_name)
            assert integration.active is True

        config_integrations_delete = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                delete: true
              slack:
                delete: true
        """

        run_gitlabform(config_integrations_delete, project)

        for integration_name in ["jira", "slack"]:
            integration = project.integrations.get(integration_name)
            assert integration.active is False

    def test__if_push_events_true_works(self, project):
        config_integration_push_events_true = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              asana:
                api_key: foo
                push_events: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_integration_push_events_true, project)

        integrations = []
        for integration_name in ["asana", "slack"]:
            integration = project.integrations.get(integration_name)
            integrations.append(integration)

        assert all([integration.active for integration in integrations]) is True
        assert all([integration.push_events for integration in integrations]) is True

    def test__if_push_events_false_works(self, project):
        config_integration_push_events_false = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              asana:
                api_key: foo
                push_events: false # changed
              slack:
                webhook: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_integration_push_events_false, project)

        integrations = []
        for integration_name in ["asana", "slack"]:
            integration = project.integrations.get(integration_name)
            integrations.append(integration)

        assert all([integration.active for integration in integrations]) is True
        assert all([integration.push_events for integration in integrations]) is False

    def test__if_push_events_change_works(self, project):
        config_integration_push_events_true = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              asana:
                api_key: foo
                push_events: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_integration_push_events_true, project)

        integrations = []
        for integration_name in ["asana", "slack"]:
            integration = project.integrations.get(integration_name)
            integrations.append(integration)

        assert all([integration.active for integration in integrations]) is True
        assert all([integration.push_events for integration in integrations]) is True

        config_integration_push_events_false = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              asana:
                api_key: foo
                push_events: false # changed
              slack:
                webhook: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_integration_push_events_false, project)

        integrations = []
        for integration_name in ["asana", "slack"]:
            integration = project.integrations.get(integration_name)
            integrations.append(integration)

        assert all([integration.active for integration in integrations]) is True
        assert all([integration.push_events for integration in integrations]) is False

    def test__if_jira_commit_events_true_works(self, project):
        config_integration_jira_commit_events_true = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_integration_jira_commit_events_true, project)

        integration = project.integrations.get("jira")
        assert integration.active is True
        assert integration.commit_events is True

    def test__if_jira_commit_events_false_works(self, project):
        config_integration_jira_commit_events_false = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_integration_jira_commit_events_false, project)

        integration = project.integrations.get("jira")
        assert integration.active is True
        assert integration.commit_events is False

    def test__if_change_works(self, project):
        config_integration_jira_commit_events_true = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_integration_jira_commit_events_true, project)

        integration = project.integrations.get("jira")
        assert integration.active is True
        assert integration.commit_events is True

        config_integration_jira_commit_events_false = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_integration_jira_commit_events_false, project)

        integration = project.integrations.get("jira")
        assert integration.active is True
        assert integration.commit_events is False

    def test__mattermost_confidential_issues_events(self, project):
        config_integration_mattermost_confidential_issues_events = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            integrations:
              mattermost:
                active: true
                webhook: https://mattermost.com/hooks/xxx
                username: gitlab
                merge_requests_events: true
                merge_request_channel: "merge-requests"
                push_events: false
                issues_events: false
                confidential_issues_events: false # this was not supposed to work according to #70
                tag_push_events: false
                note_events: false
                confidential_note_events: false
                pipeline_events: false
                wiki_page_events: false
                branches_to_be_notified: "all"
        """

        run_gitlabform(config_integration_mattermost_confidential_issues_events, project)

        integration = project.integrations.get("mattermost")
        assert integration.confidential_issues_events is False
