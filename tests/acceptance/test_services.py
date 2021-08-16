import pytest

from tests.acceptance import run_gitlabform


@pytest.fixture(scope="function")
def services(request, gitlab, group, project):
    group_and_project_name = f"{group}/{project}"

    services = ["asana", "hipchat", "redmine", "jira", "mattermost"]

    def fin():
        # disable test integrations
        for service in services:
            gitlab.delete_service(group_and_project_name, service)

    request.addfinalizer(fin)
    return services  # provide fixture value


class TestServices:
    def test__if_they_are_not_set_by_default(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        services = []
        for service_name in ["asana", "hipchat", "redmine"]:
            service = gitlab.get_service(group_and_project_name, service_name)
            services.append(service)

        assert not any([service["active"] for service in services]) is True

    def test__if_push_events_true_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_push_events_true = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              asana:
                api_key: foo
                push_events: true
              hipchat:
                token: foobar
                push_events: true
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_service_push_events_true, group_and_project_name)

        services = []
        for service_name in ["asana", "hipchat", "redmine"]:
            service = gitlab.get_service(group_and_project_name, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is True

    def test__if_push_events_false_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_push_events_false = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              asana:
                api_key: foo
                push_events: false # changed
              hipchat:
                token: foobar
                push_events: false # changed
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_service_push_events_false, group_and_project_name)

        services = []
        for service_name in ["asana", "hipchat", "redmine"]:
            service = gitlab.get_service(group_and_project_name, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is False

    def test__if_push_events_change_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_push_events_true = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              asana:
                api_key: foo
                push_events: true
              hipchat:
                token: foobar
                push_events: true
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: true
        """

        run_gitlabform(config_service_push_events_true, group_and_project_name)

        services = []
        for service_name in ["asana", "hipchat", "redmine"]:
            service = gitlab.get_service(group_and_project_name, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is True

        config_service_push_events_false = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              asana:
                api_key: foo
                push_events: false # changed
              hipchat:
                token: foobar
                push_events: false # changed
              redmine:
                new_issue_url: http://foo.bar.com
                project_url: http://foo.bar.com
                issues_url: http://foo.bar.com
                push_events: false # changed
        """

        run_gitlabform(config_service_push_events_false, group_and_project_name)

        services = []
        for service_name in ["asana", "hipchat", "redmine"]:
            service = gitlab.get_service(group_and_project_name, service_name)
            services.append(service)

        assert all([service["active"] for service in services]) is True
        assert all([service["push_events"] for service in services]) is False

    def test__if_jira_is_not_active_by_default(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is False

    def test__if_jira_commit_events_true_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_jira_commit_events_true = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_service_jira_commit_events_true, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is True
        assert service["commit_events"] is True

    def test__if_jira_commit_events_false_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_jira_commit_events_false = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_service_jira_commit_events_false, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is True
        assert service["commit_events"] is False

    def test__if_change_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_jira_commit_events_true = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_service_jira_commit_events_true, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is True
        assert service["commit_events"] is True

        config_service_jira_commit_events_false = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: false
        """

        run_gitlabform(config_service_jira_commit_events_false, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is True
        assert service["commit_events"] is False

    def test__if_delete_works(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_jira_commit_events_true = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                url: http://foo.bar.com
                username: foo
                password: bar
                active: true
                commit_events: true
        """

        run_gitlabform(config_service_jira_commit_events_true, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is True
        assert service["commit_events"] is True

        config_service_jira_delete = f"""
        projects_and_groups:
          {group_and_project_name}:
            services:
              jira:
                delete: true
        """

        run_gitlabform(config_service_jira_delete, group_and_project_name)

        service = gitlab.get_service(group_and_project_name, "jira")
        assert service["active"] is False

    def test__mattermost_confidential_issues_events(self, gitlab, group, project):
        group_and_project_name = f"{group}/{project}"

        config_service_mattermost_confidential_issues_events = f"""
        projects_and_groups:
          {group_and_project_name}:
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
            config_service_mattermost_confidential_issues_events, group_and_project_name
        )

        service = gitlab.get_service(group_and_project_name, "mattermost")
        assert service["confidential_issues_events"] is False
