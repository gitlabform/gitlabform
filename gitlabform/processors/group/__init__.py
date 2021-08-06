from typing import List

from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfiguration
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.group.group_badges_processor import GroupBadgesProcessor
from gitlabform.processors.group.group_ldap_links_processor import (
    GroupLDAPLinksProcessor,
)
from gitlabform.processors.group.group_members_processor import (
    GroupMembersProcessor,
)
from gitlabform.processors.group.group_secret_variables_processor import (
    GroupSecretVariablesProcessor,
)
from gitlabform.processors.group.group_settings_processor import (
    GroupSettingsProcessor,
)
from gitlabform.processors.group.group_shared_with_processor import (
    GroupSharedWithProcessor,
)


class GroupProcessors(object):
    def __init__(self, gitlab: GitLab):
        self.processors: List[AbstractProcessor] = [
            GroupSecretVariablesProcessor(gitlab),
            GroupSettingsProcessor(gitlab),
            GroupMembersProcessor(gitlab),
            GroupSharedWithProcessor(gitlab),
            GroupLDAPLinksProcessor(gitlab),
            GroupBadgesProcessor(gitlab),
        ]

    def get_configuration_names(self):
        return [processor.configuration_name for processor in self.processors]

    def process_group(
        self,
        group: str,
        configuration: dict,
        dry_run: bool,
        effective_configuration: EffectiveConfiguration,
    ):
        for processor in self.processors:
            processor.process(group, configuration, dry_run, effective_configuration)
