import sys
from logging import critical, info
from typing import Dict, List

from gitlab.v4.objects import Project, ProjectProtectedEnvironment

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class ProtectedEnvironmentsProcessor(AbstractProcessor):
    """https://docs.gitlab.com/ee/api/protected_environments.html#protect-repository-environments"""

    def __init__(self, gitlab: GitLab):
        super().__init__("protected_environments", gitlab)
        # deploy_access_levels is a list of dicts; compare positionally, ignoring keys
        # that GitLab adds (id, description) but the config doesn't set.
        self.custom_diff_analyzers["deploy_access_levels"] = self.recursive_diff_analyzer

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_envs: Dict = configuration.get("protected_environments", {})
        enforce = configured_envs.pop("enforce", False)

        self._find_duplicates(project_and_group, configured_envs)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_envs: List[ProjectProtectedEnvironment] = list(project.protected_environments.list(get_all=True))

        handled_names: set = set()

        for entity_name, env_config in configured_envs.items():
            name = env_config.get("name")
            if not name:
                critical(
                    f"Entity {entity_name} in protected_environments for {project_and_group}"
                    f" doesn't have its defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)

            matching = next((e for e in existing_envs if e.name == name), None)

            if env_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of protected_environments in {project_and_group}")
                    matching.delete()
                handled_names.add(name)
                continue

            self._validate_required(project_and_group, entity_name, env_config)

            if matching:
                if self._needs_update(matching.asdict(), env_config):
                    # The API doesn't support updating a protected environment, so we delete and recreate.
                    info(f" * Recreating {entity_name} of protected_environments in {project_and_group}")
                    matching.delete()
                    self._create_env(project, env_config)
                else:
                    info(
                        f" * {entity_name} of protected_environments in {project_and_group}" f" doesn't need an update."
                    )
            else:
                info(f" * Adding {entity_name} of protected_environments in {project_and_group}")
                self._create_env(project, env_config)
            handled_names.add(name)

        if enforce:
            for existing in existing_envs:
                if existing.name not in handled_names:
                    info(
                        f"Deleting protected environment '{existing.name}' in {project_and_group}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    def _create_env(
        self,
        project: Project,
        env_config: Dict,
        retry: bool = True,
    ) -> ProjectProtectedEnvironment:
        payload = {k: v for k, v in env_config.items() if k != "delete"}
        created = project.protected_environments.create(payload)

        # Workaround for https://gitlab.com/gitlab-org/gitlab/-/issues/378657:
        # GitLab occasionally returns fewer deploy_access_levels than were sent on POST.
        # Retry once by unprotecting and re-creating.
        configured_dals = payload.get("deploy_access_levels", [])
        returned_dals = getattr(created, "deploy_access_levels", []) or []
        if retry and configured_dals and len(returned_dals) != len(configured_dals):
            info("Gitlab's returned 'deploy_access_levels' differs from the sent cfg, trying again...")
            project.protected_environments.delete(payload["name"])
            return self._create_env(project, env_config, retry=False)

        return created

    @staticmethod
    def _find_duplicates(project_and_group: str, configured_envs: Dict) -> None:
        seen: Dict[str, str] = {}
        for key, entry in configured_envs.items():
            name = entry.get("name")
            if name is None:
                continue
            if name in seen:
                critical(
                    f"Entities {seen[name]} and {key} in protected_environments for {project_and_group}"
                    f" are the same in terms of their defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)
            seen[name] = key

    @staticmethod
    def _validate_required(project_and_group: str, entity_name: str, env_config: Dict) -> None:
        missing = [key for key in ("name", "deploy_access_levels") if env_config.get(key) is None]
        if missing:
            critical(
                f"Entity {entity_name} in protected_environments for {project_and_group}"
                f" doesn't have some of its keys required to create or update:"
                f" {', '.join(missing)}"
            )
            sys.exit(EXIT_INVALID_INPUT)
