from typing import List

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessors
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.project.badges_processor import BadgesProcessor
from gitlabform.processors.project.avatar_processor import AvatarProcessor
from gitlabform.processors.project.branches_processor import BranchesProcessor
from gitlabform.processors.project.deploy_keys_processor import DeployKeysProcessor
from gitlabform.processors.project.files_processor import FilesProcessor
from gitlabform.processors.project.hooks_processor import HooksProcessor
from gitlabform.processors.project.integrations_processor import IntegrationsProcessor
from gitlabform.processors.project.job_token_scope_processor import (
    JobTokenScopeProcessor,
)
from gitlabform.processors.project.members_processor import MembersProcessor
from gitlabform.processors.project.merge_requests_approval_rules import (
    MergeRequestsApprovalRules,
)
from gitlabform.processors.project.merge_requests_approvals import (
    MergeRequestsApprovals,
)
from gitlabform.processors.project.project_labels_processor import (
    ProjectLabelsProcessor,
)
from gitlabform.processors.project.project_processor import ProjectProcessor
from gitlabform.processors.project.project_push_rules_processor import (
    ProjectPushRulesProcessor,
)
from gitlabform.processors.project.project_settings_processor import (
    ProjectSettingsProcessor,
)
from gitlabform.processors.project.resource_groups_processor import (
    ResourceGroupsProcessor,
)
from gitlabform.processors.project.schedules_processor import SchedulesProcessor
from gitlabform.processors.project.tags_processor import TagsProcessor
from gitlabform.processors.project.variables_processor import VariablesProcessor
from gitlabform.processors.shared.protected_environments_processor import (
    ProtectedEnvironmentsProcessor,
)

from gitlabform.processors.project.project_security_settings import (
    ProjectSecuritySettingsProcessor,
)


class ProjectProcessors(AbstractProcessors):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__(gitlab, config, strict)
        self.processors: List[AbstractProcessor] = [
            # Order of processors matter. GitLabForm will process config sections
            # in the order listed below. Settings that are related to each other,
            # should be ordered accordingly. For example, branch protection or MR
            # approvals can configure specific users, but the user must be a
            # member of the project. So, project membership must be processed
            # before those processors.
            ProjectProcessor(gitlab),
            ProjectSettingsProcessor(gitlab, strict),
            ProjectSecuritySettingsProcessor(gitlab),
            AvatarProcessor(gitlab),
            MembersProcessor(gitlab),
            ProjectPushRulesProcessor(gitlab),
            ProjectLabelsProcessor(gitlab),
            JobTokenScopeProcessor(gitlab),
            DeployKeysProcessor(gitlab),
            VariablesProcessor(gitlab),
            BranchesProcessor(gitlab, strict),
            TagsProcessor(gitlab, strict),
            IntegrationsProcessor(gitlab),
            FilesProcessor(gitlab, config, strict),
            HooksProcessor(gitlab),
            SchedulesProcessor(gitlab),
            BadgesProcessor(gitlab),
            ResourceGroupsProcessor(gitlab),
            ProtectedEnvironmentsProcessor(gitlab),
            MergeRequestsApprovals(gitlab),
            MergeRequestsApprovalRules(gitlab),
        ]
