import enum

from typing import List

from gitlabform.gitlab.branches import GitLabBranches
from gitlabform.gitlab.commits import GitLabCommits
from gitlabform.gitlab.group_badges import GitLabGroupBadges
from gitlabform.gitlab.group_ldap_links import GitLabGroupLDAPLinks
from gitlabform.gitlab.group_variables import GitLabGroupVariables
from gitlabform.gitlab.members import GitLabMembers
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
from gitlabform.gitlab.variables import GitLabVariables
from gitlabform.gitlab.repositories import GitLabRepositories
from gitlabform.gitlab.resource_groups import GitLabResourceGroups
from gitlabform.gitlab.schedules import GitLabPipelineSchedules
from gitlabform.gitlab.integrations import GitLabIntegrations
from gitlabform.gitlab.tags import GitLabTags
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
    GitLabBranches,
    GitLabCommits,
    GitLabMergeRequests,
    GitLabRepositories,
    GitLabResourceGroups,
    GitLabIntegrations,
    GitLabTags,
    GitLabGroupLDAPLinks,
    GitLabGroupBadges,
    GitLabGroupVariables,
    GitLabPipelines,
    GitLabMembers,
    GitLabUsers,
    GitLabPipelineSchedules,
    GitLabProjectBadges,
    GitLabProjectDeployKeys,
    GitLabProjectProtectedEnvironments,
    GitLabProjectMergeRequestsApprovals,
    GitLabVariables,
):
    pass
