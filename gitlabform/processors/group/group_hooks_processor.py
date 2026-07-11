from logging import warning

from gitlab.v4.objects import Group

from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class GroupHooksProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "group_hooks",
            gitlab,
            list_method_name=self._list_hooks,
            add_method_name=self._add_hook,
            delete_method_name=self._delete_hook,
            edit_method_name=self._edit_hook,
            defining=Key("url"),
            required_to_create_or_update=Key("url"),
        )

    def _can_proceed(self, project_or_group: str, configuration: dict) -> bool:
        if not self.gitlab.enterprise:
            hooks_in_config = configuration.get("group_hooks") or {}
            if len(hooks_in_config) > 0:
                # Only warn if the user has actually configured hooks; otherwise exit silently.
                warning("GitLab Community Edition does not support Group Webhooks")
            return False
        return True

    def _process_configuration(self, group_path_and_name: str, configuration: dict):
        # The yaml alias for each hook IS the url, but the nested dict doesn't include it.
        # MultipleEntitiesProcessor matches entities via defining keys, so we inject `url` here.
        hooks = configuration.get(self.configuration_name) or {}
        for alias, hook_config in hooks.items():
            if alias == "enforce":
                continue
            if isinstance(hook_config, dict):
                hook_config.setdefault("url", alias)
        super()._process_configuration(group_path_and_name, configuration)

    def _group(self, group_path_and_name: str) -> Group:
        return self.gl.get_group_by_path_cached(group_path_and_name)

    def _list_hooks(self, group_path_and_name: str) -> list[dict]:
        return [h.asdict() for h in self._group(group_path_and_name).hooks.list(get_all=True)]

    def _add_hook(self, group_path_and_name: str, hook_config: dict) -> None:
        self._group(group_path_and_name).hooks.create(hook_config)

    def _delete_hook(self, group_path_and_name: str, hook_in_gitlab: dict) -> None:
        self._group(group_path_and_name).hooks.delete(hook_in_gitlab["id"])

    def _edit_hook(self, group_path_and_name: str, hook_in_gitlab: dict, hook_config: dict) -> None:
        self._group(group_path_and_name).hooks.update(hook_in_gitlab["id"], hook_config)
