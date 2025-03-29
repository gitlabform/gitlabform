from logging import debug
from typing import Dict, Any, List

from gitlab.base import RESTObject, RESTObjectList
from gitlab.v4.objects import Group

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupHooksProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_hooks", gitlab)

    def _process_configuration(self, group_path_and_name: str, configuration: dict):
        debug("Processing group hooks...")
        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)
        group_hooks: RESTObjectList | List[RESTObject] = group.hooks.list(get_all=True)

        hooks_in_config: tuple[str, ...] = tuple(x for x in sorted(configuration["group_hooks"]) if x != "enforce")

        for hook in hooks_in_config:
            hook_in_gitlab: RESTObject | None = next((h for h in group_hooks if h.url == hook), None)
            hook_config = {"url": hook}
            hook_config.update(configuration["group_hooks"][hook])

            hook_id = hook_in_gitlab.id if hook_in_gitlab else None

            # Process hooks configured for deletion
            if configuration.get("group_hooks|" + hook + "|delete"):
                if hook_id:
                    debug(f"Deleting group hook '{hook}'")
                    group.hooks.delete(hook_id)
                    debug(f"Deleted group hook '{hook}'")
                else:
                    debug(f"Not deleting group hook '{hook}', because it doesn't exist")
                continue

            # Process new hook creation
            if not hook_id:
                debug(f"Creating group hook '{hook}'")
                created_hook: RESTObject = group.hooks.create(hook_config)
                debug(f"Created group hook: {created_hook}")
                continue

            # Processing existing hook updates
            gl_hook: dict = hook_in_gitlab.asdict() if hook_in_gitlab else {}
            if self._needs_update(gl_hook, hook_config):
                debug(f"The group hook '{hook}' config is different from what's in gitlab OR it contains a token")
                debug(f"Updating group hook '{hook}'")
                updated_hook: Dict[str, Any] = group.hooks.update(hook_id, hook_config)
                debug(f"Updated group hook: {updated_hook}")
            else:
                debug(f"Group hook '{hook}' remains unchanged")

        # Process hook config enforcements
        if configuration.get("group_hooks|enforce"):
            for gh in group_hooks:
                if gh.url not in hooks_in_config:
                    debug(
                        f"Deleting group hook '{gh.url}' currently setup in the group but it is not in the configuration and enforce is enabled"
                    )
                    group.hooks.delete(gh.id)
