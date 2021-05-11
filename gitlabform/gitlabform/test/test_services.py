# import pytest
#
# from gitlabform.gitlab import GitLab
# from gitlabform.gitlabform import GitLabForm
# from gitlabform.gitlabform.test import (
#     create_group,
#     create_project_in_group,
#     get_gitlab,
#     GROUP_NAME,
# )
#
# PROJECT_NAME = "services_project"
# GROUP_AND_PROJECT_NAME = GROUP_NAME + "/" + PROJECT_NAME
#
#
# @pytest.fixture(scope="function")
# def gitlab(request):
#     create_group(GROUP_NAME)
#     create_project_in_group(GROUP_NAME, PROJECT_NAME)
#
#     gl = get_gitlab()
#
#     def fin():
#         # disable test integrations
#         for service in ["asana", "hipchat", "redmine", "jira", "mattermost"]:
#             gl.delete_service(GROUP_AND_PROJECT_NAME, service)
#
#     request.addfinalizer(fin)
#     return gl  # provide fixture value
#
#
# config_service_push_events_true = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       asana:
#         api_key: foo
#         push_events: true
#       hipchat:
#         token: foobar
#         push_events: true
#       redmine:
#         new_issue_url: http://foo.bar.com
#         project_url: http://foo.bar.com
#         issues_url: http://foo.bar.com
#         push_events: true
# """
#
# config_service_push_events_false = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       asana:
#         api_key: foo
#         push_events: false # changed
#       hipchat:
#         token: foobar
#         push_events: false # changed
#       redmine:
#         new_issue_url: http://foo.bar.com
#         project_url: http://foo.bar.com
#         issues_url: http://foo.bar.com
#         push_events: false # changed
# """
#
# config_service_jira_commit_events_true = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       jira:
#         url: http://foo.bar.com
#         username: foo
#         password: bar
#         active: true
#         commit_events: true
# """
#
# config_service_jira_commit_events_false = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       jira:
#         url: http://foo.bar.com
#         username: foo
#         password: bar
#         active: true
#         commit_events: false
# """
#
# config_service_jira_delete = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       jira:
#         delete: true
# """
#
# config_service_mattermost_confidential_issues_events = """
# project_settings:
#   gitlabform_tests_group/services_project:
#     services:
#       mattermost:
#         active: true
#         webhook: https://mattermost.com/hooks/xxx
#         username: gitlab
#         merge_requests_events: true
#         merge_request_channel: "merge-requests"
#         push_events: false
#         issues_events: false
#         confidential_issues_events: false # this was not supposed to work according to #70
#         tag_push_events: false
#         note_events: false
#         confidential_note_events: false
#         pipeline_events: false
#         wiki_page_events: false
#         branches_to_be_notified: "all"
# """
#
#
# class TestServices:
#     def test__if_they_are_not_set_by_default(self, gitlab):
#
#         services = []
#         for service_name in ["asana", "hipchat", "redmine"]:
#             service = gitlab.get_service(GROUP_AND_PROJECT_NAME, service_name)
#             services.append(service)
#
#         assert not any([service["active"] for service in services]) is True
#
#     def test__if_push_events_true_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_push_events_true,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         services = []
#         for service_name in ["asana", "hipchat", "redmine"]:
#             service = gitlab.get_service(GROUP_AND_PROJECT_NAME, service_name)
#             services.append(service)
#
#         assert all([service["active"] for service in services]) is True
#         assert all([service["push_events"] for service in services]) is True
#
#     def test__if_push_events_false_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_push_events_false,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         services = []
#         for service_name in ["asana", "hipchat", "redmine"]:
#             service = gitlab.get_service(GROUP_AND_PROJECT_NAME, service_name)
#             services.append(service)
#
#         assert all([service["active"] for service in services]) is True
#         assert all([service["push_events"] for service in services]) is False
#
#     def test__if_push_events_change_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_push_events_true,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         services = []
#         for service_name in ["asana", "hipchat", "redmine"]:
#             service = gitlab.get_service(GROUP_AND_PROJECT_NAME, service_name)
#             services.append(service)
#
#         assert all([service["active"] for service in services]) is True
#         assert all([service["push_events"] for service in services]) is True
#
#         gf = GitLabForm(
#             config_string=config_service_push_events_false,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         services = []
#         for service_name in ["asana", "hipchat", "redmine"]:
#             service = gitlab.get_service(GROUP_AND_PROJECT_NAME, service_name)
#             services.append(service)
#
#         assert all([service["active"] for service in services]) is True
#         assert all([service["push_events"] for service in services]) is False
#
#     def test__if_jira_is_not_active_by_default(self, gitlab):
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is False
#
#     def test__if_jira_commit_events_true_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_jira_commit_events_true,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is True
#         assert service["commit_events"] is True
#
#     def test__if_jira_commit_events_false_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_jira_commit_events_false,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is True
#         assert service["commit_events"] is False
#
#     def test__if_change_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_jira_commit_events_true,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is True
#         assert service["commit_events"] is True
#
#         gf = GitLabForm(
#             config_string=config_service_jira_commit_events_false,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is True
#         assert service["commit_events"] is False
#
#     def test__if_delete_works(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_jira_commit_events_true,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is True
#         assert service["commit_events"] is True
#
#         gf = GitLabForm(
#             config_string=config_service_jira_delete,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "jira")
#         assert service["active"] is False
#
#     def test__mattermost_confidential_issues_events(self, gitlab: GitLab):
#         gf = GitLabForm(
#             config_string=config_service_mattermost_confidential_issues_events,
#             project_or_group=GROUP_AND_PROJECT_NAME,
#         )
#         gf.main()
#
#         service = gitlab.get_service(GROUP_AND_PROJECT_NAME, "mattermost")
#         assert service["confidential_issues_events"] is False
