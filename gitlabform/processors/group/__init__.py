from typing import List

from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessors
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.group.group_badges_processor import GroupBadgesProcessor
from gitlabform.processors.group.group_ldap_links_processor import (
    GroupLDAPLinksProcessor,
)
from gitlabform.processors.group.group_members_processor import (
    GroupMembersProcessor,
)
from gitlabform.processors.group.group_saml_links_processor import (
    GroupSAMLLinksProcessor,
)
from gitlabform.processors.group.group_variables_processor import (
    GroupVariablesProcessor,
)
from gitlabform.processors.group.group_settings_processor import (
    GroupSettingsProcessor,
)
from gitlabform.processors.group.group_labels_processor import (
    GroupLabelsProcessor,
)
from gitlabform.processors.group.group_push_rules_processor import (
    GroupPushRulesProcessor,
)

from gitlabform.processors.group.group_hooks_processor import (
    GroupHooksProcessor,
)
from gitlabform.processors.group.group_protected_branches_processor import (
    GroupProtectedBranchesProcessor,
)


class GroupProcessors(AbstractProcessors):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__(gitlab, config, strict)
        self.processors: List[AbstractProcessor] = [
            GroupVariablesProcessor(gitlab),
            GroupSettingsProcessor(gitlab),
            GroupMembersProcessor(gitlab, config),
            GroupLDAPLinksProcessor(gitlab),
            GroupBadgesProcessor(gitlab),
            GroupSAMLLinksProcessor(gitlab),
            GroupLabelsProcessor(gitlab),
            GroupHooksProcessor(gitlab),
            GroupPushRulesProcessor(gitlab),
            GroupProtectedBranchesProcessor(gitlab, strict),
        ]

    def set_effective_groups(self, groups: list[str]) -> None:
        for processor in self.processors:
            if hasattr(processor, "set_effective_groups"):
                processor.set_effective_groups(groups)
