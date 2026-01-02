import logging
from urllib.parse import urlparse, urlunparse

from cli_ui import debug as verbose, info_1 as info

from gitlab.exceptions import GitlabCreateError, GitlabUpdateError, GitlabDeleteError
from gitlab.v4.objects import Project, ProjectRemoteMirror
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class RemoteMirrorsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("remote_mirrors", gitlab)
    
    @staticmethod
    def _normalize_url_for_comparison(url: str) -> str:
        """Normalize URL for comparison by removing credentials.
        
        GitLab API returns URLs with credentials scrubbed (*****), so we need to
        compare URLs without credentials to find matching mirrors.
        """
        parsed = urlparse(url)
        # Reconstruct URL without userinfo (credentials)
        normalized = urlunparse((
            parsed.scheme,
            parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        
        # 1. PREPARATION & OPTIMIZATION
        mirrors_in_gitlab: list[ProjectRemoteMirror] = project.remote_mirrors.list(get_all=True)
        gitlab_mirrors_map = {
            self._normalize_url_for_comparison(m.url): m 
            for m in mirrors_in_gitlab
        }

        mirrors_in_config: dict = configuration.get("remote_mirrors", {}).copy()
        enforce_mirrors = mirrors_in_config.pop("enforce", False)
        urls_to_keep = set()

        # 2. PROCESS CONFIGURATION
        for mirror_url in sorted(mirrors_in_config.keys()):
            mirror_settings = mirrors_in_config[mirror_url]
            norm_url = self._normalize_url_for_comparison(mirror_url)
            mirror_in_gitlab = gitlab_mirrors_map.get(norm_url)

            # --- CASE: EXPLICIT DELETE ---
            if mirror_settings.get("delete"):
                if mirror_in_gitlab:
                    self._delete_remote_mirror(mirror_in_gitlab)
                    gitlab_mirrors_map.pop(norm_url, None)
                else:
                    verbose(f"Skip deleting remote mirror '{norm_url}', because it doesn't exist")
                continue

            # --- CASE: CREATE OR UPDATE ---
            urls_to_keep.add(norm_url)
            
            # Prepare payload: Start with URL and update with config settings
            mirror_payload: dict = {"url": mirror_url, **mirror_settings}
            
            # Extract local-only options
            force_push = mirror_payload.pop("force_push", False)
            force_update = mirror_payload.pop("force_update", False)
            mirror_payload.pop("delete", None)

            if mirror_in_gitlab:
                # Update existing mirror if needed
                self._update_existing_mirror(project, mirror_in_gitlab, mirror_payload, norm_url, force_update)
            else:
                # Create new mirror
                mirror_in_gitlab = self._create_new_mirror(project, mirror_payload, mirror_url)

            # Optionally force a sync (force-push) if requested in config
            if force_push and mirror_in_gitlab:
                self._sync_remote_mirror(project, mirror_in_gitlab)

        # 3. ENFORCEMENT PHASE (Implicit Cleanup)
        if enforce_mirrors:
            self._enforce_mirrors(gitlab_mirrors_map, urls_to_keep)

    def _needs_update(self, existing_mirror: ProjectRemoteMirror, config_payload: dict) -> bool:
        """
        Overrides the base comparison to handle GitLab's URL credential masking.
        Normalization is applied so that 'user:pass@host' matches '*****:*****@host'.
        Note: force_update is handled in _update_existing_mirror to allow for specific logging.
        """
        comparison_payload = config_payload.copy()
        if "url" in comparison_payload:
            comparison_payload["url"] = self._normalize_url_for_comparison(comparison_payload["url"])
            
        existing_mirror_dict = existing_mirror.asdict().copy()
        existing_mirror_dict["url"] = self._normalize_url_for_comparison(existing_mirror_dict["url"])
        
        return super()._needs_update(existing_mirror_dict, comparison_payload)

    def _update_existing_mirror(self, project: Project, mirror_obj: ProjectRemoteMirror, payload: dict, norm_url: str, force_update: bool):
        """Compares and updates an existing mirror if changed or if force_update is set."""
        
        should_update = force_update or self._needs_update(mirror_obj, payload)

        if should_update:
            if force_update:
                verbose(f"Mirror '{norm_url}' update is being forced via 'force_update' flag.")
            
            verbose(f"Updating remote mirror '{norm_url}' with latest config")
            try:
                project.remote_mirrors.update(id=mirror_obj.id, new_data=payload)
                verbose(f"Updated remote mirror '{norm_url}'")
                
                if force_update:
                    info(f"!!! REMINDER: 'force_update' was used for mirror '{norm_url}'. "
                         "Please remove this flag from your configuration to avoid unnecessary API calls in future runs.")
            except GitlabUpdateError:
                logging.exception("Failed to update remote mirror %s", payload.get("url"))
        else:
            verbose(f"Remote mirror '{norm_url}' remains unchanged")

    def _create_new_mirror(self, project: Project, payload: dict, raw_url: str) -> ProjectRemoteMirror | None:
        """Creates a new remote mirror and handles API errors."""
        verbose(f"Creating remote mirror '{raw_url}'")
        try:
            return project.remote_mirrors.create(payload)
        except GitlabCreateError:
            logging.exception("Failed to create remote mirror %s", raw_url)
            return None

    def _enforce_mirrors(self, gitlab_mirrors_map: dict, urls_to_keep: set):
        """Deletes mirrors present in GitLab that are not in the 'keep' configuration."""
        for norm_url, gm in gitlab_mirrors_map.items():
            if norm_url not in urls_to_keep:
                verbose(f"Enforce: Deleting remote mirror '{gm.url}' as it is not in the 'keep' configuration")
                self._delete_remote_mirror(gm)

    def _delete_remote_mirror(self, mirror: ProjectRemoteMirror):
        """Delete the given `ProjectRemoteMirror` and handle errors."""
        verbose(f"Deleting remote mirror '{mirror.url}'")
        try:
            mirror.delete()
        except GitlabDeleteError:
            logging.exception("Failed to delete remote mirror id=%s url=%s", getattr(mirror, "id", None), getattr(mirror, "url", None))
            verbose(f"Failed to delete remote mirror '{mirror.url}'")

    def _sync_remote_mirror(self, project: Project, mirror: ProjectRemoteMirror):
        """Trigger sync for remote mirror when `force_push` is requested."""
        mirror_id = getattr(mirror, "id", None)
        mirror_url = getattr(mirror, "url", None)
        verbose(f"Attempting sync for remote mirror id={mirror_id} url={mirror_url}")

        try:
            result = mirror.sync()
            verbose(f"Triggered sync for remote mirror '{mirror_url}' result={result}")
        except Exception:
            logging.exception("Failed to trigger sync for remote mirror id=%s url=%s", mirror_id, mirror_url)
            verbose(f"Failed to trigger sync for remote mirror '{mirror_url}'")
