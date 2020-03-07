import pytest

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform import GitLabForm
from gitlabform.gitlabform.test import create_group, create_project_in_group, get_gitlab, GROUP_NAME

PROJECT_NAME = 'services_project'
GROUP_AND_PROJECT_NAME = GROUP_NAME + '/' + PROJECT_NAME


@pytest.fixture(scope="function")
def gitlab(request):
    create_group(GROUP_NAME)
    create_project_in_group(GROUP_NAME, PROJECT_NAME)

    gl = get_gitlab()

    def fin():
        # disable test integrations
        gl.delete_service(GROUP_AND_PROJECT_NAME, 'jira')

    request.addfinalizer(fin)
    return gl  # provide fixture value


config_service_jira_commit_events_true = """
gitlab:
  api_version: 4
project_settings:
  gitlabform_tests_group/services_project:
    services:
      jira:
        url: http://foo.bar.com
        username: foo
        password: bar
        active: true
        commit_events: true
"""

config_service_jira_commit_events_false = """
gitlab:
  api_version: 4
project_settings:
  gitlabform_tests_group/services_project:
    services:
      jira:
        url: http://foo.bar.com
        username: foo
        password: bar
        active: true
        commit_events: true
"""

# config_service_mattermost_confidential_issues_events = """
# gitlab:
#   api_version: 4
#
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


class TestServices:

    def test__if_it_is_not_set_by_default(self, gitlab):
        service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'asana')
        assert service['active'] is False

    def test__if_jira_commit_events_true_works(self, gitlab: GitLab):
        gf = GitLabForm(config_string=config_service_jira_commit_events_true, project_or_group=GROUP_AND_PROJECT_NAME, debug=True)
        gf.main()

        service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'jira')
        assert service['commit_events'] is True

    def test__if_jira_commit_events_false_works(self, gitlab: GitLab):
        gf = GitLabForm(config_string=config_service_jira_commit_events_false, project_or_group=GROUP_AND_PROJECT_NAME, debug=True)
        gf.main()

        service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'jira')
        assert service['commit_events'] is False

    def test__if_change_works(self, gitlab: GitLab):
        gf = GitLabForm(config_string=config_service_jira_commit_events_true, project_or_group=GROUP_AND_PROJECT_NAME, debug=True)
        gf.main()

        service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'jira')
        assert service['commit_events'] is True

        gf = GitLabForm(config_string=config_service_jira_commit_events_false, project_or_group=GROUP_AND_PROJECT_NAME, debug=True)
        gf.main()

        service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'jira')
        assert service['commit_events'] is False

    # def test__mattermost_confidential_issues_events(self, gitlab: GitLab):
    #     gf = GitLabForm(config_string=config_service_mattermost_confidential_issues_events,
    #                     project_or_group=GROUP_AND_PROJECT_NAME)
    #     gf.main()
    #
    #     service = gitlab.get_service(GROUP_AND_PROJECT_NAME, 'mattermost')
    #     assert service['confidential_issues_events'] is False
