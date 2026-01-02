import enum

from typing import List

from gitlab import GraphQL

from gitlabform.gitlab.commits import GitLabCommits
from gitlabform.gitlab.group_badges import GitLabGroupBadges
from gitlabform.gitlab.group_ldap_links import GitLabGroupLDAPLinks
from gitlabform.gitlab.group_variables import GitLabGroupVariables
from gitlabform.gitlab.merge_requests import GitLabMergeRequests
from gitlabform.gitlab.pipelines import GitLabPipelines
from gitlabform.gitlab.project_badges import GitLabProjectBadges
from gitlabform.gitlab.project_deploy_keys import GitLabProjectDeployKeys
from gitlabform.gitlab.project_protected_environments import (
    GitLabProjectProtectedEnvironments,
)
from gitlabform.gitlab.project_merge_requests_approvals import (
    GitLabProjectMergeRequestsApprovals,
)
from gitlabform.gitlab.python_gitlab import PythonGitlab
from gitlabform.gitlab.variables import GitLabVariables
from gitlabform.gitlab.project_security_settings import GitlabProjectSecuritySettings


@enum.unique
class AccessLevel(enum.IntEnum):
    NO_ACCESS = 0
    MINIMAL = 5  # introduced in GitLab 13.5
    GUEST = 10
    PLANNER = 15  # introduced in GitLab 17.7
    REPORTER = 20
    DEVELOPER = 30
    MAINTAINER = 40
    OWNER = 50  # only for groups
    ADMIN = 60

    @classmethod
    def group_levels(cls) -> List[int]:
        return [level.value for level in AccessLevel if level <= 50]

    @classmethod
    def get_value(cls, name: str) -> int:
        # for the above set of key names this is enough for an effectively fuzzy name matching
        return AccessLevel[name.strip().upper().replace(" ", "_")].value

    @classmethod
    def get_canonical_names(cls) -> List[str]:
        return [level.name.lower().replace("_", " ") for level in AccessLevel]


class GitLab(
    GitLabCommits,
    GitLabMergeRequests,
    GitLabGroupLDAPLinks,
    GitLabGroupBadges,
    GitLabGroupVariables,
    GitLabPipelines,
    GitLabProjectBadges,
    GitLabProjectDeployKeys,
    GitLabProjectProtectedEnvironments,
    GitLabProjectMergeRequestsApprovals,
    GitLabVariables,
    GitlabProjectSecuritySettings,
):
    pass


class GitlabWrapper:
    # Parameters accepted by python-gitlab's Gitlab.__init__
    # Other config keys (like max_retries) are used elsewhere in gitlabform
    # or passed to specific components like GraphQL
    GITLAB_CLIENT_PARAMS = {
        "url",
        "private_token",
        "oauth_token",
        "job_token",
        "ssl_verify",
        "http_username",
        "http_password",
        "timeout",
        "api_version",
        "per_page",
        "pagination",
        "order_by",
        "user_agent",
        "retry_transient_errors",
        "keep_base_url",
    }

    # Parameters accepted by python-gitlab's GraphQL.__init__
    GRAPHQL_PARAMS = {
        "ssl_verify",
        "client",
        "timeout",
        "user_agent",
        "fetch_schema_from_transport",
        "max_retries",
        "obey_rate_limit",
        "retry_transient_errors",
    }

    def __init__(self, gitlabform: GitLab):
        session = gitlabform.session

        graphql_kwargs = {k: v for k, v in gitlabform.gitlab_config.items() if k in self.GRAPHQL_PARAMS}
        graphql = GraphQL(
            url=gitlabform.gitlab_config["url"],
            token=gitlabform.gitlab_config["token"],
            **graphql_kwargs,
        )

        default_kwargs = {
            "retry_transient_errors": True,
        }
        renamed_kwargs = {
            "token": "private_token",
        }
        extra_kwargs = {
            **default_kwargs,
            **{
                k: v
                for k, v in gitlabform.gitlab_config.items()
                if k not in renamed_kwargs and k in self.GITLAB_CLIENT_PARAMS
            },
            **{renamed_kwargs[k]: v for k, v in gitlabform.gitlab_config.items() if k in renamed_kwargs},
        }

        self._gitlab: PythonGitlab = PythonGitlab(
            api_version="4",
            graphql=graphql,
            session=session,
            **extra_kwargs,
        )

    def get_gitlab(self):
        return self._gitlab
