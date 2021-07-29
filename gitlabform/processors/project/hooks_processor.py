import logging
import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class HooksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("hooks")
        self.gitlab = gitlab

    def _process_configuration(
        self, project_and_group: str, configuration: dict, do_apply: bool = True
    ):
        for hook in sorted(configuration["hooks"]):

            if configuration.get("hooks|" + hook + "|delete"):
                hook_id = self.gitlab.get_hook_id(project_and_group, hook)
                if hook_id:
                    logging.debug(f"Deleting hook '{hook}'")
                    self.gitlab.delete_hook(project_and_group, hook_id)
                else:
                    logging.debug(
                        f"Not deleting hook '{hook}', because it doesn't exist"
                    )
            else:
                hook_id = self.gitlab.get_hook_id(project_and_group, hook)
                if hook_id:
                    logging.debug(f"Changing existing hook '{hook}'")
                    self.gitlab.put_hook(
                        project_and_group, hook_id, hook, configuration["hooks"][hook]
                    )
                else:
                    logging.debug(f"Creating hook '{hook}'")
                    self.gitlab.post_hook(
                        project_and_group, hook, configuration["hooks"][hook]
                    )
