from logging import debug
from typing import Dict, Any, List

from gitlab.base import RESTObject, RESTObjectList
from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class HooksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("hooks", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        debug("Processing hooks...")
        project: Project = self.gl.projects.get(project_and_group)
        hooks_list: RESTObjectList | List[RESTObject] = project.hooks.list()

        for hook in sorted(configuration["hooks"]):
            hook_id = next((h.id for h in hooks_list if h.url == hook), None)
            if configuration.get("hooks|" + hook + "|delete"):
                if hook_id:
                    debug("Deleting hook '%s'", hook)
                    project.hooks.delete(hook_id)
                else:
                    debug("Not deleting hook '%s', because it doesn't exist", hook)
            else:
                hook_config = {"url": hook}
                hook_config.update(configuration["hooks"][hook])
                if hook_id:
                    debug("Changing existing hook '%s'", hook)
                    changed_hook: Dict[str, Any] = project.hooks.update(
                        hook_id, hook_config
                    )
                    debug("Changed hook to '%s'", changed_hook)
                else:
                    debug("Creating hook '%s'", hook)
                    created_hook: RESTObject = project.hooks.create(hook_config)
                    debug("Created hook '%s'", created_hook)
