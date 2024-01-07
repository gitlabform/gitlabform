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
        config_hooks = filter(lambda x: x != "enforce", sorted(configuration["hooks"]))

        for hook in config_hooks:
            gitlab_hook: RESTObject | None = next(
                (h for h in hooks_list if h.url == hook), None
            )
            hook_id = gitlab_hook.id if gitlab_hook else None
            if configuration.get("hooks|" + hook + "|delete"):
                if hook_id:
                    debug("Deleting hook '%s'", hook)
                    project.hooks.delete(hook_id)
                else:
                    debug("Not deleting hook '%s', because it doesn't exist", hook)
            else:
                hook_config = {"url": hook}
                hook_config.update(configuration["hooks"][hook])
                gl_hook_dict = gitlab_hook.asdict() if gitlab_hook else {}
                diffs = (
                    map(
                        lambda k: hook_config[k] != gl_hook_dict[k],
                        hook_config.keys(),
                    )
                    if gl_hook_dict
                    else iter(())
                )
                if not hook_id:
                    debug("Creating hook '%s'", hook)
                    created_hook: RESTObject = project.hooks.create(hook_config)
                    debug("Created hook '%s'", created_hook)
                elif hook_id and any(diffs):
                    debug("Changing existing hook '%s'", hook)
                    changed_hook: Dict[str, Any] = project.hooks.update(
                        hook_id, hook_config
                    )
                    debug("Changed hook to '%s'", changed_hook)
                elif hook_id and not any(diffs):
                    debug(f"Hook {hook} remains unchanged")

        if configuration.get("hooks|enforce"):
            for gh in hooks_list:
                if gh.url not in config_hooks:
                    debug(
                        "Deleting hook '%s' currently setup in the project but it is not in the configuration and enforce is enabled",
                        gh.url,
                    )
                    project.hooks.delete(gh.id)
