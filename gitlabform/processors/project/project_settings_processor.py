from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class ProjectSettingsProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "project_settings",
            gitlab,
            get_method_name="get_project_settings",
            edit_method_name="put_project_settings",
        )
