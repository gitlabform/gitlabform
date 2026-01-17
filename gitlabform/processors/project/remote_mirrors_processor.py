from typing import Any, cast, Dict, Set, List, Optional
from urllib.parse import urlparse

from cli_ui import debug as verbose, info_1 as info, warning

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

        Given a mirror URL for password-based authentication,
        this method returns the corresponding URL without credentials.

        Example:
        http://username:password@host/path.git -> http://host/path.git

        This can be used to compare mirror URLs without credentials to
        find matching mirrors.
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        # Remove credentials (user:pass@) from netloc
        clean_netloc = parsed.netloc.split("@")[-1]
        return parsed._replace(netloc=clean_netloc).geturl()

    def _process_configuration(self, project_and_group: str, configuration: Dict[str, Any]) -> None:
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        # 1. PREPARATION & OPTIMIZATION
        mirrors_in_gitlab: List[ProjectRemoteMirror] = project.remote_mirrors.list(get_all=True)
        gitlab_mirrors_map: Dict[str, ProjectRemoteMirror] = {
            self._normalize_url_for_comparison(m.url): cast(ProjectRemoteMirror, m) for m in mirrors_in_gitlab
        }

        mirrors_in_config: Dict[str, Any] = configuration.get("remote_mirrors", {}).copy()

        # --- GLOBAL OPTIONS ---
        enforce_mirrors: bool = mirrors_in_config.pop("enforce", False)
        print_details: bool = mirrors_in_config.pop("print_details", False)

        urls_to_keep: Set[str] = set()

        # 2. PROCESS CONFIGURATION (Create / Update / Delete)
        for mirror_url in sorted(mirrors_in_config.keys()):
            mirror_settings: Dict[str, Any] = mirrors_in_config[mirror_url]
            norm_url: str = self._normalize_url_for_comparison(mirror_url)
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

            # Prepare payload: Extract local-only options
            mirror_payload: Dict[str, Any] = {"url": mirror_url, **mirror_settings}
            force_push: bool = mirror_payload.pop("force_push", False)
            force_update: bool = mirror_payload.pop("force_update", False)
            print_public_key: bool = mirror_payload.pop("print_public_key", False)
            mirror_payload.pop("delete", None)

            if mirror_in_gitlab:
                self._update_existing_mirror(project, mirror_in_gitlab, mirror_payload, norm_url, force_update)
            else:
                mirror_in_gitlab = self._create_new_mirror(project, mirror_payload, mirror_url)

            if print_public_key and mirror_in_gitlab:
                self._handle_public_key_display(project, mirror_in_gitlab, norm_url)

            if force_push and mirror_in_gitlab:
                self._sync_remote_mirror(mirror_in_gitlab)

        # 3. ENFORCEMENT PHASE
        if enforce_mirrors:
            self._enforce_mirrors(gitlab_mirrors_map, urls_to_keep)

        # 4. REPORTING PHASE (Final State)
        if print_details:
            # We fetch a fresh list to show the final state after all updates/syncs
            final_mirrors: List[ProjectRemoteMirror] = project.remote_mirrors.list(get_all=True)
            if not final_mirrors:
                info("🔍 No remote mirrors found for this project.")
            else:
                info(f"📋 Final Remote Mirror Report for '{project_and_group}':")
                for mirror in final_mirrors:
                    info("  " + "─" * 30)  # Visual separator using a light line
                    self._report_mirror_details(mirror)
                info("  " + "─" * 30)

    def _handle_public_key_display(self, project: Project, mirror_obj: ProjectRemoteMirror, norm_url: str) -> None:
        """
        Retrieves and prints the SSH public key for a mirror.
        GitLab only provides this for mirrors configured with 'ssh_public_key' auth.
        """
        # Only attempt retrieval if the auth method supports it
        if getattr(mirror_obj, "auth_method", None) != "ssh_public_key":
            verbose(f"Skipping public key display for '{norm_url}': auth_method is not 'ssh_public_key'")
            return

        public_key: Optional[str] = None
        try:
            # TODO: python-gitlab does not yet support retrieving the public key via
            # ProjectRemoteMirror object (e.g., mirror_obj.get_public_key()).
            # Switch to native method once supported in the library.

            # Mypy fix: cast the union return type (dict | Response) to dict[str, Any]
            response = cast(
                Dict[str, Any],
                project.manager.gitlab.http_get(f"/projects/{project.id}/remote_mirrors/{mirror_obj.id}/public_key"),
            )
            public_key = response.get("public_key")
        except Exception as e:
            warning(f"Failed to retrieve SSH public key for mirror {norm_url}: {e}")

        if public_key:
            info(f"🔑 SSH Public Key for mirror '{norm_url}':")
            info(public_key)
            info("👆 This public key must be added to the target repository to authorize the mirror.")
            info(
                "Please consult the GitLab documentation on 'Repository Mirroring' for specific setup instructions for your target platform."
            )
        else:
            verbose(f"No public key available to display for mirror '{norm_url}'")

    def _needs_update(self, existing_mirror: Dict[str, Any], config_payload: Dict[str, Any]) -> bool:
        """
        Overrides the base comparison to handle GitLab's URL credential masking.
        Normalization is applied so that 'user:pass@host' matches '*****:*****@host'.
        """
        comparison_payload: Dict[str, Any] = config_payload.copy()
        if "url" in comparison_payload:
            comparison_payload["url"] = self._normalize_url_for_comparison(comparison_payload["url"])

        existing_mirror_dict = existing_mirror.copy()

        existing_mirror_dict["url"] = self._normalize_url_for_comparison(existing_mirror_dict.get("url", ""))

        return super()._needs_update(existing_mirror_dict, comparison_payload)

    def _update_existing_mirror(
        self,
        project: Project,
        mirror_obj: ProjectRemoteMirror,
        payload: Dict[str, Any],
        norm_url: str,
        force_update: bool,
    ) -> None:
        """Compares and updates an existing mirror if changed or if force_update is set."""

        should_update: bool = force_update or self._needs_update(mirror_obj.asdict(), payload)

        if should_update:
            if force_update:
                verbose(f"Mirror '{norm_url}' update is being forced via 'force_update' flag.")

            verbose(f"Updating remote mirror '{norm_url}' with latest config")
            try:
                project.remote_mirrors.update(id=mirror_obj.id, new_data=payload)
                verbose(f"Updated remote mirror '{norm_url}'")

                if force_update:
                    info(
                        f"!!! REMINDER: 'force_update' was used for mirror '{norm_url}'. "
                        "Please remove this flag from your configuration to avoid unnecessary API calls in future runs."
                    )
            except GitlabUpdateError as e:
                warning(f"Failed to update remote mirror {norm_url}: {e}")
        else:
            verbose(f"Remote mirror '{norm_url}' remains unchanged")

    def _create_new_mirror(
        self, project: Project, payload: Dict[str, Any], raw_url: str
    ) -> Optional[ProjectRemoteMirror]:
        """Creates a new remote mirror and handles API errors."""
        norm_url = self._normalize_url_for_comparison(raw_url)
        verbose(f"Creating remote mirror '{norm_url}'")
        try:
            return cast(ProjectRemoteMirror, project.remote_mirrors.create(payload))
        except GitlabCreateError as e:
            warning(f"Failed to create remote mirror {norm_url}: {e}")
            return None

    def _enforce_mirrors(self, gitlab_mirrors_map: Dict[str, ProjectRemoteMirror], urls_to_keep: Set[str]) -> None:
        """Deletes mirrors present in GitLab that are not in the configuration."""
        for norm_url, gm in gitlab_mirrors_map.items():
            if norm_url not in urls_to_keep:
                verbose(f"Enforce: Deleting remote mirror '{gm.url}' as it is not in the configuration")
                self._delete_remote_mirror(gm)

    def _delete_remote_mirror(self, mirror: ProjectRemoteMirror) -> None:
        """Delete the given `ProjectRemoteMirror` and handle errors."""
        verbose(f"Deleting remote mirror '{mirror.url}'")
        try:
            mirror.delete()
        except GitlabDeleteError as e:
            warning(
                f"Failed to delete remote mirror id={getattr(mirror, 'id', None)} url={getattr(mirror, 'url', None)}: {e}"
            )
            verbose(f"Failed to delete remote mirror '{mirror.url}'")

    def _sync_remote_mirror(self, mirror: ProjectRemoteMirror) -> None:
        """Trigger sync for remote mirror when `force_push` is requested."""
        mirror_id = getattr(mirror, "id", None)
        mirror_url = getattr(mirror, "url", None)
        verbose(f"Attempting sync for remote mirror id={mirror_id} url={mirror_url}")

        try:
            result = mirror.sync()
            verbose(f"Triggered sync for remote mirror '{mirror_url}' result={result}")
        except Exception as e:
            info(f"Failed to trigger sync for remote mirror id={mirror_id} url={mirror_url}: {e}")
            # verbose(f"Failed to trigger sync for remote mirror '{mirror_url}'")

    def _report_mirror_details(self, mirror: ProjectRemoteMirror) -> None:
        """Prints every attribute of the mirror object, one per line."""

        mirror_data = mirror.asdict()

        # Mapping statuses to helpful visual cues
        status_icons = {
            "finished": "✅",
            "started": "⏳",
            "scheduled": "📅",
            "failed": "❌",
            "none": "⚪",
        }

        for key, value in sorted(mirror_data.items()):
            if key == "update_status":
                icon = status_icons.get(value, "❓")
                info(f"    - {key}: {icon} {value}")
            elif key == "last_error" and value:
                info(f"    - {key}: ⚠️ {value}")
            else:
                info(f"    - {key}: {value}")
