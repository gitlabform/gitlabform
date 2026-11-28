from typing import Dict, List

from gitlab.v4.objects import Project, ProjectProtectedEnvironment

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.protected_environments import (
    ExistingProtectedEnvironment,
    sync_protected_environments,
)


class ProtectedEnvironmentsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("protected_environments", gitlab)
        # deploy_access_levels and approval_rules are lists of dicts; compare positionally,
        # ignoring keys that GitLab adds (id, description) but the config doesn't set.
        self.custom_diff_analyzers["deploy_access_levels"] = self.recursive_diff_analyzer
        self.custom_diff_analyzers["approval_rules"] = self.recursive_diff_analyzer

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_objects: List[ProjectProtectedEnvironment] = project.protected_environments.list(get_all=True)
        existing_envs: List[ExistingProtectedEnvironment] = [
            (env.name, env.asdict(), env.delete) for env in existing_objects
        ]

        sync_protected_environments(
            configuration_name=self.configuration_name,
            entity_path=project_and_group,
            configured_envs=configuration.get("protected_environments", {}),
            existing_envs=existing_envs,
            create_env=project.protected_environments.create,
            needs_update=self._needs_update,
        )
