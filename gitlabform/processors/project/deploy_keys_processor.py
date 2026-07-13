import sys
from logging import critical, info
from typing import Dict, List, Optional

from gitlab.exceptions import GitlabCreateError
from gitlab.v4.objects import Project, ProjectKey

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployKeysProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_keys", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_keys: Dict = configuration.get("deploy_keys", {})
        enforce = configured_keys.pop("enforce", False)

        self._find_duplicates(project_and_group, configured_keys)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_keys: List[ProjectKey] = list(project.keys.list(get_all=True))

        handled_titles: set = set()

        for entity_name, key_config in configured_keys.items():
            title = key_config.get("title")
            if not title:
                critical(
                    f"Entity {entity_name} in deploy_keys for {project_and_group}"
                    f" doesn't have its defining key: 'title'"
                )
                sys.exit(EXIT_INVALID_INPUT)

            matching = next((k for k in existing_keys if k.title == title), None)

            if key_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of deploy_keys in {project_and_group}")
                    matching.delete()
                handled_titles.add(title)
                continue

            self._validate_required(project_and_group, entity_name, key_config)

            if matching:
                if self._needs_update(matching.asdict(), key_config):
                    # The GitLab API cannot update a deploy key's value (only title/can_push),
                    # so we delete and recreate to allow full replacement.
                    info(f" * Recreating {entity_name} of deploy_keys in {project_and_group}")
                    matching.delete()
                    self._create_or_enable(project, key_config)
                else:
                    info(f" * {entity_name} of deploy_keys in {project_and_group} doesn't need an update.")
            else:
                info(f" * Adding {entity_name} of deploy_keys in {project_and_group}")
                self._create_or_enable(project, key_config)
            handled_titles.add(title)

        if enforce:
            for existing in existing_keys:
                if existing.title not in handled_titles:
                    info(
                        f"Deleting deploy key '{existing.title}' in {project_and_group}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    def _create_or_enable(self, project: Project, key_config: Dict) -> None:
        try:
            project.keys.create(key_config)
        except GitlabCreateError as e:
            # GitLab sometimes returns HTTP 400 with "has already been taken" when adding an SSH key
            # that already exists on another project, despite the docs saying it should just associate.
            # As a workaround, look up the existing key on the instance and enable it for this project.
            if e.response_code != 400 or "has already been taken" not in str(e):
                raise

            existing_id = self._find_existing_deploy_key_id(key_config["key"])
            if existing_id is None:
                raise
            project.keys.enable(existing_id)

    def _find_existing_deploy_key_id(self, configured_key: str) -> Optional[int]:
        for existing in self.gl.deploykeys.list(get_all=True):
            if self._keys_are_effectively_equal(existing.key, configured_key):
                return existing.id
        return None

    @staticmethod
    def _keys_are_effectively_equal(key1: str, key2: str) -> bool:
        # We ignore the comment part of the SSH key: GitLab doesn't allow adding the same key
        # with a different comment, but it also has a bug where returned keys have truncated
        # comments when the comment contains spaces, so a naive compare can show a false diff.
        parts1 = key1.split(" ", 2)
        parts2 = key2.split(" ", 2)
        if len(parts1) < 2 or len(parts2) < 2:
            return False
        return parts1[0] == parts2[0] and parts1[1] == parts2[1]

    @staticmethod
    def _find_duplicates(project_and_group: str, configured_keys: Dict) -> None:
        seen: Dict[str, str] = {}
        for key, entry in configured_keys.items():
            title = entry.get("title")
            if title is None:
                continue
            if title in seen:
                critical(
                    f"Entities {seen[title]} and {key} in deploy_keys for {project_and_group}"
                    f" are the same in terms of their defining key: 'title'"
                )
                sys.exit(EXIT_INVALID_INPUT)
            seen[title] = key

    @staticmethod
    def _validate_required(project_and_group: str, entity_name: str, key_config: Dict) -> None:
        missing = [key for key in ("title", "key") if not key_config.get(key)]
        if missing:
            critical(
                f"Entity {entity_name} in deploy_keys for {project_and_group}"
                f" doesn't have some of its keys required to create or update:"
                f" {', '.join(missing)}"
            )
            sys.exit(EXIT_INVALID_INPUT)
