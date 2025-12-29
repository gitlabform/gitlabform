import logging
from urllib.parse import urlparse, urlunparse

from cli_ui import debug as verbose

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
    
    def _get_mirror_by_url(self, project: Project, mirror_url: str) -> ProjectRemoteMirror | None:
        """
        Given a mirror URL, this method returns the corresponding ProjectRemoteMirror object if found, otherwise None.
        GitLabForm config for mirror URL may have embedded credentials for password-based authentication.
        GitLab API returns URLs with credentials scrubbed (*****), so we need to use URLs without credentials to find matching mirror.
        """
        normalized_config_url = self._normalize_url_for_comparison(mirror_url)
        mirrors_in_gitlab: list[ProjectRemoteMirror] = project.remote_mirrors.list(get_all=True)
        for mirror in mirrors_in_gitlab:
            normalized_gitlab_url = self._normalize_url_for_comparison(mirror.url)
            if normalized_gitlab_url == normalized_config_url:
                return mirror
        return None

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        mirrors_in_config: dict = configuration.get("remote_mirrors", {})
        mirrors_in_gitlab: list[ProjectRemoteMirror] = project.remote_mirrors.list(get_all=True)
        enforce_mirrors: bool = configuration.get("remote_mirrors|enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "remote_mirror"
        if enforce_mirrors:
            mirrors_in_config.pop("enforce")

        # Mirrors that are in the configuration and also in GitLab should be updated if config changed.
        # Mirrors that are in the configuration but not in GitLab should be created.
        # Mirrors that are not in the configuration but are in GitLab should be deleted if "enforce" is set.
        for mirror_url in sorted(mirrors_in_config.keys()):
            mirror_in_config = mirrors_in_config[mirror_url]
            # Start with URL and update with all config - this follows GitLabForm's pattern
            # where config keys match GitLab API payload parameters
            mirror_config: dict = {"url": mirror_url}
            mirror_config.update(mirror_in_config)
            
            # Extract local-only options so they are not passed to the API.
            # force_push: triggers a sync after create/update (uses POST /projects/:id/remote_mirrors/:mirror_id/sync)
            force_push = mirror_config.pop("force_push", False)

            # Normalize URLs for comparison since GitLab returns URLs with scrubbed credentials
            # normalized_config_url = self._normalize_url_for_comparison(mirror_url)
            mirror_in_gitlab: ProjectRemoteMirror | None = self._get_mirror_by_url(project, mirror_url)

            # Delete if requested
            if configuration.get(f"remote_mirrors|{mirror_url}|delete"):
                if mirror_in_gitlab:
                    self._delete_remote_mirror(mirror_in_gitlab)
                else:
                    verbose(f"Skip deleting remote mirror '{mirror_url}', because it doesn't exist")
                continue

            if mirror_in_gitlab:
                # Update existing mirror if needed
                # Before we compare mirror configuration, we need to normalize the URL.
                # GitLabForm config contains credentials but GitLab's response scrubs the credentials.
                # So for true comparison, we need to remove the credentials from both.

                mirror_config_temp = mirror_config.copy()
                mirror_config_temp["url"] = self._normalize_url_for_comparison(mirror_config_temp["url"])

                mirror_in_gitlab_temp = mirror_in_gitlab.asdict().copy()
                mirror_in_gitlab_temp["url"] = self._normalize_url_for_comparison(mirror_in_gitlab_temp["url"])

                if self._needs_update(mirror_in_gitlab_temp, mirror_config_temp):
                    verbose(f"The remote mirror '{mirror_config_temp['url']}' config is different from what's in gitlab")
                    verbose(f"Updating remote mirror '{mirror_config_temp['url']}' with latest config")
                    try:
                        updated_mirror = project.remote_mirrors.update(id = mirror_in_gitlab.id, new_data = mirror_config)
                        verbose(f"Updated remote mirror: id={mirror_in_gitlab.id} config={updated_mirror}")
                    except GitlabUpdateError:
                        verbose(f"Failed to update remote mirror '{updated_mirror}'")
                else:
                    verbose(f"Remote mirror '{mirror_config_temp['url']}' remains unchanged")
            else:
                # Create new mirror
                verbose(f"Creating remote mirror '{mirror_url}' with config: {mirror_config}")
                try:
                    mirror_in_gitlab = project.remote_mirrors.create(mirror_config)
                    try:
                        verbose(f"Created remote mirror: id={mirror_in_gitlab.id} url={mirror_in_gitlab.url} config={mirror_in_gitlab.asdict()}")
                    except Exception:
                        verbose(f"Created remote mirror: {mirror_in_gitlab}")
                except GitlabCreateError:
                    logging.exception("Failed to create remote mirror %s", mirror_url)
                    verbose(f"Failed to create remote mirror '{mirror_url}'")
                    mirror_in_gitlab = None

            # Optionally force a sync (force-push) if requested in config
            if force_push and mirror_in_gitlab:
                self._sync_remote_mirror(project, mirror_in_gitlab)

        # Process enforcement: delete mirrors present in GitLab but not in config
        # Refresh the mirrors list to get the current state after all create/update/delete operations
        if enforce_mirrors:
            mirrors_in_gitlab = project.remote_mirrors.list(get_all=True)
            # Normalize config URLs for comparison
            normalized_config_urls = {self._normalize_url_for_comparison(url) for url in mirrors_in_config.keys()}
            for gm in mirrors_in_gitlab:
                normalized_gitlab_url = self._normalize_url_for_comparison(gm.url)
                if normalized_gitlab_url not in normalized_config_urls:
                    verbose(
                        f"Deleting remote mirror '{gm.url}' currently setup in the project but it is not in the configuration and enforce is enabled"
                    )
                    self._delete_remote_mirror(gm)

    def _delete_remote_mirror(self, mirror: ProjectRemoteMirror):
        """Delete the given `ProjectRemoteMirror` and handle errors.

        This helper expects a `ProjectRemoteMirror` object and will call its
        `.delete()` method. It logs success or failure; callers should only
        call it when a mirror object is available.
        """
        verbose(f"Deleting remote mirror '{mirror.url}'")
        try:
            mirror.delete()
            verbose(f"Deleted remote mirror '{mirror.url}'")
        except GitlabDeleteError:
            logging.exception("Failed to delete remote mirror id=%s url=%s", getattr(mirror, "id", None), getattr(mirror, "url", None))
            verbose(f"Failed to delete remote mirror '{mirror.url}'")

    def _sync_remote_mirror(self, project: Project, mirror: ProjectRemoteMirror):
        """Trigger sync for remote mirror when `force_push` is requested, with logging.
        
        Uses python-gitlab's sync() method as documented:
        https://python-gitlab.readthedocs.io/en/stable/gl_objects/remote_mirrors.html
        
        Tries mirror.sync() first, falls back to manager method if needed.
        """
        mirror_id = getattr(mirror, "id", None)
        mirror_url = getattr(mirror, "url", None)
        verbose(f"Attempting sync for remote mirror id={mirror_id} url={mirror_url}")

        try:
            result = mirror.sync()
            verbose(f"Triggered sync for remote mirror '{mirror_url}' result={result}")
        except Exception as error:
            logging.exception("Failed to trigger sync for remote mirror id=%s url=%s", getattr(mirror, "id", None), getattr(mirror, "url", None))
            verbose(f"Failed to trigger sync for remote mirror '{mirror.url}'")
            verbose(f"Error details: {error}")
        
        # Refresh the mirror object to get the latest state
        refreshed_mirror: ProjectRemoteMirror | None = self._get_mirror_by_url(project, mirror.url)
        if refreshed_mirror:
            verbose(f"Mirror state after sync: {refreshed_mirror.asdict()}")
        else:
            verbose(f"Failed to refresh mirror object after sync for remote mirror '{mirror.url}'")

