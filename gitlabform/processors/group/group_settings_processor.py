from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class GroupSettingsProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_settings",
            gitlab,
            get_method_name="get_group_settings",
            edit_method_name="put_group_settings",
        )
