import functools
from typing import Any, Dict, List, cast
from urllib.parse import quote

from gitlab.v4.objects import Group

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.protected_environments import (
    ExistingProtectedEnvironment,
    sync_protected_environments,
)


class GroupProtectedEnvironmentsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_protected_environments", gitlab)
        # deploy_access_levels and approval_rules are lists of dicts; compare positionally,
        # ignoring keys that GitLab adds (id, description, null fields) but the config doesn't set.
        self.custom_diff_analyzers["deploy_access_levels"] = self.recursive_diff_analyzer
        self.custom_diff_analyzers["approval_rules"] = self.recursive_diff_analyzer

    def _process_configuration(self, group_path_and_name: str, configuration: Dict):
        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)
        existing_envs: List[ExistingProtectedEnvironment] = [
            (
                env["name"],
                env,
                functools.partial(self._delete_protected_environment, group, env["name"]),
            )
            for env in self._list_protected_environments(group)
        ]

        sync_protected_environments(
            configuration_name=self.configuration_name,
            entity_path=group_path_and_name,
            configured_envs=configuration.get("group_protected_environments", {}),
            existing_envs=existing_envs,
            create_env=functools.partial(self._create_protected_environment, group),
            needs_update=self._needs_update,
        )

    def _list_protected_environments(self, group: Group) -> List[Dict[str, Any]]:
        # TODO: python-gitlab does not yet expose a dedicated manager for group-level
        # protected environments, so use lower-level HTTP helpers until supported natively.
        path = f"/groups/{group.id}/protected_environments"
        return cast(List[Dict[str, Any]], self.gl.http_list(path, get_all=True))

    def _create_protected_environment(self, group: Group, env_config: Dict[str, Any]) -> None:
        path = f"/groups/{group.id}/protected_environments"
        self.gl.http_post(path, post_data=env_config)

    def _delete_protected_environment(self, group: Group, name: str) -> None:
        encoded_name = quote(name, safe="")
        path = f"/groups/{group.id}/protected_environments/{encoded_name}"
        self.gl.http_delete(path)
