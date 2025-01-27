from gitlabform.gitlab import GitLab
from gitlabform.processors.single_entity_processor import SingleEntityProcessor


class ProjectSecuritySettingsProcessor(SingleEntityProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "project_security_settings",
            gitlab,
            get_method_name="get_project_security_settings",
            edit_method_name="put_project_security_settings",
        )
