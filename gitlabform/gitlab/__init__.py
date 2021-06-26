import enum
from enum import Enum

from gitlabform.gitlab.branches import GitLabBranches
from gitlabform.gitlab.commits import GitLabCommits
from gitlabform.gitlab.groups import GitLabGroups
from gitlabform.gitlab.members import GitLabMembers
from gitlabform.gitlab.merge_requests import GitLabMergeRequests
from gitlabform.gitlab.pipelines import GitLabPipelines
from gitlabform.gitlab.projects import GitLabProjects
from gitlabform.gitlab.repositories import GitLabRepositories
from gitlabform.gitlab.schedules import GitLabPipelineSchedules
from gitlabform.gitlab.services import GitLabServices
from gitlabform.gitlab.tags import GitLabTags
from gitlabform.gitlab.users import GitLabUsers


@enum.unique
class AccessLevel(Enum):
    NO_ACCESS = 0
    MINIMAL = 5  # introduced in GitLab 13.5
    GUEST = 10
    REPORTER = 20
    DEVELOPER = 30
    MAINTAINER = 40
    OWNER = 50  # only for groups
    ADMIN = 60


class GitLab(
    GitLabBranches,
    GitLabCommits,
    GitLabMergeRequests,
    GitLabProjects,
    GitLabRepositories,
    GitLabServices,
    GitLabTags,
    GitLabGroups,
    GitLabPipelines,
    GitLabMembers,
    GitLabUsers,
    GitLabPipelineSchedules,
):
    pass
