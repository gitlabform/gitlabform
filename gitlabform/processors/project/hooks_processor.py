from logging import debug

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class HooksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("hooks", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for hook in sorted(configuration["hooks"]):
            if configuration.get("hooks|" + hook + "|delete"):
                hook_id = self.gitlab.get_hook_id(project_and_group, hook)
                if hook_id:
                    debug("Deleting hook '%s'", hook)
                    self.gitlab.delete_hook(project_and_group, hook_id)
                else:
                    debug("Not deleting hook '%s', because it doesn't exist", hook)
            else:
                hook_id = self.gitlab.get_hook_id(project_and_group, hook)
                if hook_id:
                    debug("Changing existing hook '%s'", hook)
                    self.gitlab.put_hook(
                        project_and_group, hook_id, hook, configuration["hooks"][hook]
                    )
                else:
                    debug("Creating hook '%s'", hook)
                    self.gitlab.post_hook(
                        project_and_group, hook, configuration["hooks"][hook]
                    )
