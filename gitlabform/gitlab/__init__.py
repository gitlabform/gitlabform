from gitlabform import Singleton
from gitlabform.gitlab.branches import GitLabBranches
from gitlabform.gitlab.commits import GitLabCommits
from gitlabform.gitlab.groups import GitLabGroups
from gitlabform.gitlab.merge_requests import GitLabMergeRequests
from gitlabform.gitlab.projects import GitLabProjects
from gitlabform.gitlab.repositories import GitLabRepositories
from gitlabform.gitlab.services import GitLabServices
from gitlabform.gitlab.tags import GitLabTags
from gitlabform.gitlab.pipelines import GitLabPipelines
from gitlabform.gitlab.members import GitLabMembers
from gitlabform.gitlab.users import GitLabUsers


class GitLab(GitLabBranches, GitLabCommits, GitLabMergeRequests, GitLabProjects, GitLabRepositories, GitLabServices,
             GitLabTags, GitLabGroups, GitLabPipelines, GitLabMembers, GitLabUsers,
             metaclass=Singleton):
    pass
