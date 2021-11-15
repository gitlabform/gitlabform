from cli_ui import warning

from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfiguration
from gitlabform.processors.abstract_processor import AbstractProcessor


from gitlabform.processors.util.decorators import configuration_to_safe_dict


# this processor exists only to prevent the configs with just `group_shared_with` key on a group
# level to not be processed because of an empty effective config
class GroupSharedWithProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_shared_with", gitlab)

    @configuration_to_safe_dict
    def process(
        self,
        project_or_project_and_group: str,
        configuration: dict,
        dry_run: bool,
        effective_configuration: EffectiveConfiguration,
    ):
        pass

    def _process_configuration(self, group: str, configuration: dict):
        pass
