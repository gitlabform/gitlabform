import pytest

from gitlabform.gitlab.core import NotFoundException
from tests.acceptance import run_gitlabform


@pytest.fixture(scope="function")
def services(request, gitlab, group_and_project):

    services = ["asana", "slack", "redmine", "jira", "mattermost"]

    def fin():
        # disable test integrations
        for service in services:
            gitlab.delete_service(group_and_project, service)

    request.addfinalizer(fin)
    return services  # provide fixture value


class TestServices:
    # we use "other_project" here on purpose because if we would reuse the "project"
    # then we could end up with running this test after another, and a service created
    # and then deleted is a different entity in GitLab than a never created one (!).
    # the first one exists but has "active" field set to False, the other throws 404
    def test__if_they_are_not_set_by_default(self, gitlab, group, other_project):
        group_and_project = f"{group}/{other_project}"

        for service_name in ["asana", "slack", "redmine", "jira"]:
            with pytest.raises(NotFoundException):
                gitlab.get_service(group_and_project, service_name)

    def test__if_delete_works(self, gitlab, group_and_project):

        config_services = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
              asana:
                api_key: foo
                push_events: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_services, group_and_project)

        for service_name in ["jira", "asana", "slack", "redmine"]:
            service = gitlab.get_service(group_and_project, service_name)
            assert service["active"] is True

        config_services_delete = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                delete: true
              slack:
                delete: true
        """

        run_gitlabform(config_services_delete, group_and_project)

        for service_name in ["jira", "slack"]:
            service = gitlab.get_service(group_and_project, service_name)
            assert service["active"] is False

    def test__if_push_events_true_works(self, gitlab, group_and_project):

        config_service_push_events_true = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              asana:
                api_key: foo
                push_events: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_service_push_events_true, group_and_project)

        services = []
        for service_name in ["asana", "slack", "redmine"]:
            service = gitlab.get_service(group_and_project, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is True

    def test__if_push_events_false_works(self, gitlab, group_and_project):

        config_service_push_events_false = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              asana:
                api_key: foo
                push_events: false # changed
              slack:
                webhook: http://foo.bar.com
                push_events: false # changed
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_service_push_events_false, group_and_project)

        services = []
        for service_name in ["asana", "slack", "redmine"]:
            service = gitlab.get_service(group_and_project, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is False

    def test__if_push_events_change_works(self, gitlab, group_and_project):

        config_service_push_events_true = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              asana:
                api_key: foo
                push_events: true
              slack:
                webhook: http://foo.bar.com
                push_events: true
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_service_push_events_true, group_and_project)

        services = []
        for service_name in ["asana", "slack", "redmine"]:
            service = gitlab.get_service(group_and_project, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is True

        config_service_push_events_false = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              asana:
                api_key: foo
                push_events: false # changed
              slack:
                webhook: http://foo.bar.com
                push_events: false # changed
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_service_push_events_false, group_and_project)

        services = []
        for service_name in ["asana", "slack", "redmine"]:
            service = gitlab.get_service(group_and_project, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is False

    def test__if_jira_commit_events_true_works(self, gitlab, group_and_project):

        config_service_jira_commit_events_true = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_service_jira_commit_events_true, group_and_project)

        service = gitlab.get_service(group_and_project, "jira")
        assert service["active"] is True
        assert service["commit_events"] is True

    def test__if_jira_commit_events_false_works(self, gitlab, group_and_project):

        config_service_jira_commit_events_false = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_service_jira_commit_events_false, group_and_project)

        service = gitlab.get_service(group_and_project, "jira")
        assert service["active"] is True
        assert service["commit_events"] is False

    def test__if_change_works(self, gitlab, group_and_project):

        config_service_jira_commit_events_true = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_service_jira_commit_events_true, group_and_project)

        service = gitlab.get_service(group_and_project, "jira")
        assert service["active"] is True
        assert service["commit_events"] is True

        config_service_jira_commit_events_false = f"""
        projects_and_groups:
          {group_and_project}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_service_jira_commit_events_false, group_and_project)

        service = gitlab.get_service(group_and_project, "jira")
        assert service["active"] is True
        assert service["commit_events"] is False

    def test__mattermost_confidential_issues_events(self, gitlab, group_and_project):

        config_service_mattermost_confidential_issues_events = f"""
        projects_and_groups:
          {group_and_project}:
            services:
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

        run_gitlabform(
            config_service_mattermost_confidential_issues_events, group_and_project
        )

        service = gitlab.get_service(group_and_project, "mattermost")
        assert service["confidential_issues_events"] is False
