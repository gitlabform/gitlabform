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
    GroupPushRulesProcessor
)

class GroupProcessors(AbstractProcessors):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__(gitlab, config, strict)
        self.processors: List[AbstractProcessor] = [
            GroupVariablesProcessor(gitlab),
            GroupSettingsProcessor(gitlab),
            GroupMembersProcessor(gitlab),
            GroupLDAPLinksProcessor(gitlab),
            GroupBadgesProcessor(gitlab),
            GroupSAMLLinksProcessor(gitlab),
            GroupLabelsProcessor(gitlab),
            GroupPushRulesProcessor(gitlab),
        ]
