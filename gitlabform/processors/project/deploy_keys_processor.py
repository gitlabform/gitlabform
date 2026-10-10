from logging import info
from typing import Dict, List, Optional

from gitlab.exceptions import GitlabCreateError
from gitlab.v4.objects import Project, ProjectKey

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployKeysProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_keys", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict):
        configured_keys: Dict = configuration.get("deploy_keys", {})
        enforce = configured_keys.pop("enforce", False)

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        existing_keys: List[ProjectKey] = project.keys.list(get_all=True)

        # The two loops below delete before anything is added, because a deploy key's value is
        # unique within the instance: adding a key back under another title only succeeds once
        # the key under the old title is gone.
        if enforce:
            configured_titles = {key_config["title"] for key_config in configured_keys.values()}
            for existing in existing_keys:
                if existing.title not in configured_titles:
                    info(
                        f"Deleting deploy key '{existing.title}' of {self.configuration_name} in {project_and_group}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()

        for entity_name, key_config in configured_keys.items():
            if not key_config.get("delete", False):
                continue

            title = key_config["title"]

            matching = next((k for k in existing_keys if k.title == title), None)

            if matching:
                info(f"Deleting {entity_name} of {self.configuration_name} in {project_and_group}")
                matching.delete()
            else:
                info(
                    f"Not deleting {entity_name} of {self.configuration_name} in {project_and_group},"
                    f" because it doesn't exist"
                )

        for entity_name, key_config in configured_keys.items():
            if key_config.get("delete", False):
                continue

            title = key_config["title"]

            matching = next((k for k in existing_keys if k.title == title), None)

            if matching:
                if self._needs_update(matching.asdict(), key_config):
                    # The GitLab API can only update a deploy key's title and can_push, not its value
                    # (https://docs.gitlab.com/api/deploy_keys/#update-a-deploy-key), so we recreate it.
                    info(f" * Recreating {entity_name} of {self.configuration_name} in {project_and_group}")
                    matching.delete()
                    self._create_or_enable(project, key_config)
                else:
                    info(
                        f" * {entity_name} of {self.configuration_name} in {project_and_group} doesn't need an update."
                    )
            else:
                info(f" * Adding {entity_name} of {self.configuration_name} in {project_and_group}")
                self._create_or_enable(project, key_config)

    def _create_or_enable(self, project: Project, key_config: Dict) -> None:
        try:
            project.keys.create(key_config)
        except GitlabCreateError as e:
            # GitLab sometimes returns HTTP 400 with "has already been taken" when adding an SSH key
            # that already exists on another project, despite the docs saying it should just associate.
            # As a workaround, look up the existing key on the instance and enable it for this project.
            key_already_exists = e.response_code == 400 and "has already been taken" in str(e)
            if not key_already_exists:
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
