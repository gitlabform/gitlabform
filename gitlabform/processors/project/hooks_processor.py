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
        project_hooks: RESTObjectList | List[RESTObject] = project.hooks.list()
        hooks_in_config: tuple[str, ...] = tuple(
            x for x in sorted(configuration["hooks"]) if x != "enforce"
        )

        for hook in hooks_in_config:
            hook_in_gitlab: RESTObject | None = next(
                (h for h in project_hooks if h.url == hook), None
            )
            hook_id = hook_in_gitlab.id if hook_in_gitlab else None
            if configuration.get("hooks|" + hook + "|delete"):
                if hook_id:
                    debug(f"Deleting hook '{hook}'")
                    project.hooks.delete(hook_id)
                else:
                    debug(f"Not deleting hook '{hook}', because it doesn't exist")
            else:
                hook_config = {"url": hook}
                hook_config.update(configuration["hooks"][hook])
                if not hook_id:
                    debug(f"Creating hook '{hook}'")
                    created_hook: RESTObject = project.hooks.create(hook_config)
                    debug(f"Created hook: {created_hook}")
                else:
                    if "token" in hook_config:
                        debug(
                            f"The hook '{hook}' config includes a token. Diff between config vs gitlab cannot be confirmed"
                        )
                        debug(f"Updating hook '{hook}'")
                        updated_hook: Dict[str, Any] = project.hooks.update(
                            hook_id, hook_config
                        )
                        debug(f"Updated hook: {updated_hook}")
                    else:
                        gl_hook: dict = (
                            hook_in_gitlab.asdict() if hook_in_gitlab else {}
                        )
                        diffs = (
                            map(
                                lambda k: hook_config[k] != gl_hook[k],
                                hook_config.keys(),
                            )
                            if gl_hook
                            else iter(())
                        )
                        if hook_id and any(diffs):
                            debug(
                                f"The hook '{hook}' config is different from what's in gitlab"
                            )
                            debug(f"Updating hook '{hook}'")
                            updated_hook = project.hooks.update(hook_id, hook_config)
                            debug(f"Updated hook: {updated_hook}")
                        elif hook_id and not any(diffs):
                            debug(f"Hook '{hook}' remains unchanged")

        if configuration.get("hooks|enforce"):
            for gh in project_hooks:
                if gh.url not in hooks_in_config:
                    debug(
                        f"Deleting hook '{gh.url}' currently setup in the project but it is not in the configuration and enforce is enabled"
                    )
                    project.hooks.delete(gh.id)
