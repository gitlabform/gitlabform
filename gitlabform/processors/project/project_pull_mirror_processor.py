from typing import Any, Dict, Optional
from logging import info, warning

from gitlab.exceptions import GitlabCreateError, GitlabGetError, GitlabUpdateError
from gitlab.v4.objects import Project, ProjectPullMirror
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.mirrors import (
    mask_mirror_url_credentials,
    normalize_mirror_url_for_comparison,
)


class ProjectPullMirrorProcessor(AbstractProcessor):
    """
    A processor for the "pull_mirror" configuration section.

    Manages pull mirroring of a project using the dedicated Pull Mirroring API
    (GitLab Premium, 17.6+), which replaces the deprecated way of configuring
    pull mirroring through the project edit API.
    See: https://docs.gitlab.com/api/project_pull_mirroring/

    A project can have only one pull mirror, so the section is a flat map of
    settings. GitLabForm follows the "raw parameter passing" pattern, so any
    parameter supported by the GitLab API can be used here, e.g.:
    url, enabled, auth_user, auth_password, mirror_trigger_builds,
    only_mirror_protected_branches, mirror_overwrites_diverged_branches,
    mirror_branch_regex.

    Additionally, the following GitLabForm-specific keys are supported:
    * force_update: (boolean) If true, forces an update call even if the config
      looks unchanged (useful for updating credentials, which GitLab masks).
    * force_pull: (boolean) If true, triggers an immediate pull sync.

    The API provides no way to delete a pull mirror; set "enabled: false" to
    stop mirroring.

    Configuration example:

    pull_mirror:
      url: "https://username:token@example.com/some/repo.git"
      enabled: true
      only_mirror_protected_branches: false
    """

    def __init__(self, gitlab: GitLab):
        super().__init__("pull_mirror", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        mirror_payload: Dict[str, Any] = (configuration.get("pull_mirror") or {}).copy()

        force_update: bool = mirror_payload.pop("force_update", False)
        force_pull: bool = mirror_payload.pop("force_pull", False)

        mirror_in_gitlab: Optional[ProjectPullMirror] = None
        if mirror_payload or force_pull:
            mirror_in_gitlab = self._get_pull_mirror(project)

        if mirror_payload:
            if mirror_in_gitlab:
                self._update_existing_mirror(project, mirror_in_gitlab, mirror_payload, force_update)
            elif "url" in mirror_payload:
                mirror_in_gitlab = self._create_new_mirror(project, mirror_payload)
            else:
                info("Skip configuring pull mirror, because it doesn't exist and no 'url' is set")

        if force_pull:
            if mirror_in_gitlab:
                self._sync_pull_mirror(project)
            else:
                info("Skip triggering pull mirror sync, because the project has no pull mirror")

    def _get_pull_mirror(self, project: Project) -> Optional[ProjectPullMirror]:
        try:
            return project.pull_mirror.get()
        except GitlabGetError as e:
            if e.response_code == 404:
                return None
            raise

    def _needs_update(self, existing_mirror: Dict[str, Any], config_payload: Dict[str, Any]) -> bool:
        """
        Overrides the base comparison to handle GitLab's URL credential masking
        and the auth attributes, which GitLab never returns and so cannot be
        compared (use force_update to change credentials).
        """
        comparison_payload: Dict[str, Any] = config_payload.copy()
        comparison_payload.pop("auth_user", None)
        comparison_payload.pop("auth_password", None)
        if "url" in comparison_payload:
            comparison_payload["url"] = normalize_mirror_url_for_comparison(comparison_payload["url"])

        existing_mirror_dict = existing_mirror.copy()
        existing_mirror_dict["url"] = normalize_mirror_url_for_comparison(existing_mirror_dict.get("url") or "")

        return super()._needs_update(existing_mirror_dict, comparison_payload)

    def _update_existing_mirror(
        self,
        project: Project,
        mirror_in_gitlab: ProjectPullMirror,
        payload: Dict[str, Any],
        force_update: bool,
    ) -> None:
        should_update: bool = force_update or self._needs_update(mirror_in_gitlab.asdict(), payload)

        if should_update:
            if force_update:
                info("Pull mirror update is being forced via 'force_update' flag.")

            info("Updating pull mirror with latest config")
            try:
                project.pull_mirror.update(new_data=payload)
                info("Updated pull mirror")

                if force_update:
                    info(
                        "!!! REMINDER: 'force_update' was used for the pull mirror. "
                        "Please remove this flag from your configuration to avoid unnecessary API calls in future runs."
                    )
            except GitlabUpdateError as e:
                warning(f"Failed to update pull mirror: {e}")
        else:
            info("Pull mirror remains unchanged")

    def _create_new_mirror(self, project: Project, payload: Dict[str, Any]) -> Optional[ProjectPullMirror]:
        info("Creating pull mirror")
        try:
            mirror = project.pull_mirror.create(payload)
            info("Created pull mirror")
            return mirror
        except GitlabCreateError as e:
            warning(f"Failed to create pull mirror: {e}")
            return None

    def _sync_pull_mirror(self, project: Project) -> None:
        info("Triggering pull mirror sync")
        try:
            project.pull_mirror.start()
            info("Triggered pull mirror sync")
        except Exception as e:
            warning(f"Failed to trigger pull mirror sync: {e}")

    def _get_current_state(self, project_and_group: str) -> dict:
        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        mirror = self._get_pull_mirror(project)
        return mirror.asdict() if mirror else {}

    def _get_desired_state(self, entity_config: dict) -> dict:
        # mask the secrets, as the diff is printed; GitLab masks them the same
        # way in the current state
        desired = dict(entity_config or {})
        desired.pop("force_update", None)
        desired.pop("force_pull", None)
        if desired.get("auth_password"):
            desired["auth_password"] = "*****"
        if desired.get("url"):
            desired["url"] = mask_mirror_url_credentials(desired["url"])
        return desired
