from logging import info
from typing import Dict, List

from gitlab.v4.objects import Project, ProjectProtectedEnvironment

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ProtectedEnvironmentsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("protected_environments", gitlab)
        # deploy_access_levels is a list of dicts; compare positionally, ignoring keys
        # that GitLab adds (id, description) but the config doesn't set.
        self.custom_diff_analyzers["deploy_access_levels"] = self.recursive_diff_analyzer

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_envs: Dict = configuration.get("protected_environments", {})
        enforce = configured_envs.pop("enforce", False)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_envs: List[ProjectProtectedEnvironment] = project.protected_environments.list(get_all=True)

        processed_names: set = set()

        for entity_name, env_config in configured_envs.items():
            name = env_config["name"]
            matching = next((env for env in existing_envs if env.name == name), None)

            if env_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of {self.configuration_name} in {project_and_group}")
                    matching.delete()
                else:
                    info(
                        f"Not deleting {entity_name} of {self.configuration_name} in {project_and_group},"
                        f" because it doesn't exist"
                    )
                processed_names.add(name)
                continue

            if matching:
                if self._needs_update(matching.asdict(), env_config):
                    # The API has an update endpoint (https://docs.gitlab.com/api/protected_environments/),
                    # but python-gitlab's ProjectProtectedEnvironmentManager doesn't support it, so we recreate.
                    info(f" * Recreating {entity_name} of {self.configuration_name} in {project_and_group}")
                    matching.delete()
                    self._create_env(project, env_config)
                else:
                    info(
                        f" * {entity_name} of {self.configuration_name} in {project_and_group}"
                        f" doesn't need an update."
                    )
            else:
                info(f" * Adding {entity_name} of {self.configuration_name} in {project_and_group}")
                self._create_env(project, env_config)
            processed_names.add(name)

        if enforce:
            for existing in existing_envs:
                if existing.name not in processed_names:
                    info(
                        f"Deleting protected environment '{existing.name}' of {self.configuration_name}"
                        f" in {project_and_group} as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    def _create_env(self, project: Project, env_config: Dict, retry: bool = True) -> None:
        created = project.protected_environments.create(env_config)

        # Workaround for https://gitlab.com/gitlab-org/gitlab/-/issues/378657:
        # GitLab sometimes applies fewer deploy_access_levels than were sent,
        # so we unprotect the environment and try once more.
        configured_levels = env_config.get("deploy_access_levels", [])
        returned_levels = getattr(created, "deploy_access_levels", None) or []
        if retry and configured_levels and len(returned_levels) != len(configured_levels):
            info("Gitlab's returned 'deploy_access_levels' differs from the sent cfg, trying again...")
            created.delete()
            self._create_env(project, env_config, retry=False)
