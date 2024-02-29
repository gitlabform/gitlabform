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
            hook_config = {"url": hook}
            hook_config.update(configuration["hooks"][hook])

            hook_id = hook_in_gitlab.id if hook_in_gitlab else None

            # Process hooks configured for deletion
            if configuration.get("hooks|" + hook + "|delete"):
                if hook_id:
                    debug(f"Deleting hook '{hook}'")
                    project.hooks.delete(hook_id)
                    debug(f"Deleted hook '{hook}'")
                else:
                    debug(f"Not deleting hook '{hook}', because it doesn't exist")
                continue

            # Process new hook creation
            if not hook_id:
                debug(f"Creating hook '{hook}'")
                created_hook: RESTObject = project.hooks.create(hook_config)
                debug(f"Created hook: {created_hook}")
                continue

            # Processing existing hook updates
            gl_hook: dict = hook_in_gitlab.asdict() if hook_in_gitlab else {}
            if self.is_hook_config_different(gl_hook, hook_config):
                debug(
                    f"The hook '{hook}' config is different from what's in gitlab OR it contains a token"
                )
                debug(f"Updating hook '{hook}'")
                updated_hook: Dict[str, Any] = project.hooks.update(
                    hook_id, hook_config
                )
                debug(f"Updated hook: {updated_hook}")
            else:
                debug(f"Hook '{hook}' remains unchanged")

        # Process hook config enforcements
        if configuration.get("hooks|enforce"):
            for gh in project_hooks:
                if gh.url not in hooks_in_config:
                    debug(
                        f"Deleting hook '{gh.url}' currently setup in the project but it is not in the configuration and enforce is enabled"
                    )
                    project.hooks.delete(gh.id)

    def is_hook_config_different(
        self, config_in_gitlab: dict, config_in_gitlabform: dict
    ):
        """
        Compare two dictionary representing a webhook configuration and determine
        if they are different.

        GitLab's webhook data does not contain "token" as it is considered a secret.
        If GitLabForm config for a webhook contains a "token", the difference cannot
        be validated. In this case, the config is assumed to be different. Otherwise,
        the config data will be compared and determined if they are different.

        Args:
            config_in_gitlab (dict): hook configuration in gitlab
            config_in_gitlabform (dict): hook configuration in gitlabform

        Returns:
            boolean: True if the two configs are different. Otherwise False.
        """
        if "token" in config_in_gitlabform:
            debug(
                f"The hook '{config_in_gitlabform['url']}' config includes a token. Diff between config vs gitlab cannot be confirmed."
            )
            return True

        diffs = (
            map(
                lambda k: config_in_gitlabform[k] != config_in_gitlab[k],
                config_in_gitlabform.keys(),
            )
            if config_in_gitlab
            else iter(())
        )

        if any(diffs):
            return True
        else:
            return False
