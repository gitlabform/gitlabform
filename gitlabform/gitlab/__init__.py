import enum

from typing import List

from gitlabform.gitlab.commits import GitLabCommits
from gitlabform.gitlab.group_badges import GitLabGroupBadges
from gitlabform.gitlab.group_ldap_links import GitLabGroupLDAPLinks
from gitlabform.gitlab.group_variables import GitLabGroupVariables
from gitlabform.gitlab.group_push_rules import GitLabGroupPushRules
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
from gitlabform.gitlab.users import GitLabUsers


@enum.unique
class AccessLevel(enum.IntEnum):
    NO_ACCESS = 0
    MINIMAL = 5  # introduced in GitLab 13.5
    GUEST = 10
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
    GitLabGroupPushRules,
    GitLabPipelines,
    GitLabUsers,
    GitLabProjectBadges,
    GitLabProjectDeployKeys,
    GitLabProjectProtectedEnvironments,
    GitLabProjectMergeRequestsApprovals,
    GitLabVariables,
):
    pass


class GitlabWrapper:
    def __init__(self, gitlabform: GitLab):
        url = gitlabform.url
        token = gitlabform.token
        ssl_verify = gitlabform.ssl_verify
        timeout = gitlabform.timeout
        session = gitlabform.session

        self._gitlab: PythonGitlab = PythonGitlab(
            url,
            token,
            ssl_verify=ssl_verify,
            api_version="4",
            session=session,
            retry_transient_errors=True,
            timeout=timeout,
        )

    def get_gitlab(self):
        return self._gitlab
