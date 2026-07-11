from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class HooksProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "hooks",
            gitlab,
            list_method_name=self._list_hooks,
            add_method_name=self._add_hook,
            delete_method_name=self._delete_hook,
            edit_method_name=self._edit_hook,
            defining=Key("url"),
            required_to_create_or_update=Key("url"),
        )

    def _process_configuration(self, project_and_group: str, configuration: dict):
        # The yaml alias for each hook IS the url, but the nested dict doesn't include it.
        # MultipleEntitiesProcessor matches entities via defining keys, so we inject `url` here.
        hooks = configuration.get(self.configuration_name) or {}
        for alias, hook_config in hooks.items():
            if alias == "enforce":
                continue
            if isinstance(hook_config, dict):
                hook_config.setdefault("url", alias)
        super()._process_configuration(project_and_group, configuration)

    def _project(self, project_and_group: str) -> Project:
        return self.gl.get_project_by_path_cached(project_and_group)

    def _list_hooks(self, project_and_group: str) -> list[dict]:
        return [h.asdict() for h in self._project(project_and_group).hooks.list(get_all=True)]

    def _add_hook(self, project_and_group: str, hook_config: dict) -> None:
        self._project(project_and_group).hooks.create(hook_config)

    def _delete_hook(self, project_and_group: str, hook_in_gitlab: dict) -> None:
        self._project(project_and_group).hooks.delete(hook_in_gitlab["id"])

    def _edit_hook(self, project_and_group: str, hook_in_gitlab: dict, hook_config: dict) -> None:
        self._project(project_and_group).hooks.update(hook_in_gitlab["id"], hook_config)
