from cli_ui import debug as verbose

from gitlab.exceptions import GitlabCreateError, GitlabUpdateError, GitlabDeleteError
from gitlab.v4.objects import Project, ProjectRemoteMirror
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class RemoteMirrorsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("remote_mirrors", gitlab)

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
            mirror_config: dict = {"url": mirror_url}
            mirror_config.update(mirror_in_config)
            # Extract local-only options so they are not passed to the API.
            force_push = mirror_config.pop("force_push", False)

            mirror_in_gitlab: ProjectRemoteMirror | None = next(
                (m for m in mirrors_in_gitlab if m.url == mirror_url), None
            )

            # Delete if requested
            if configuration.get(f"remote_mirrors|{mirror_url}|delete"):
                if mirror_in_gitlab:
                    self._delete_remote_mirror(mirror_in_gitlab)
                else:
                    verbose(f"Skip deleting remote mirror '{mirror_url}', because it doesn't exist")
                continue

            if mirror_in_gitlab:
                # Update existing mirror if needed
                if self._needs_update(mirror_in_gitlab.asdict(), mirror_config):
                    verbose(f"The remote mirror '{mirror_url}' config is different from what's in gitlab")
                    verbose(f"Updating remote mirror '{mirror_url}'")
                    try:
                        mirror_in_gitlab.update(**mirror_config)
                        verbose(f"Updated remote mirror: {mirror_in_gitlab}")
                    except GitlabUpdateError:
                        verbose(f"Failed to update remote mirror '{mirror_url}'")
                else:
                    verbose(f"Remote mirror '{mirror_url}' remains unchanged")
            else:
                # Create new mirror
                verbose(f"Creating remote mirror '{mirror_url}'")
                try:
                    mirror_in_gitlab = project.remote_mirrors.create(mirror_config)
                    verbose(f"Created remote mirror: {mirror_in_gitlab}")
                except GitlabCreateError:
                    verbose(f"Failed to create remote mirror '{mirror_url}'")

            # Optionally force a sync (force-push) if requested in config
            if force_push and mirror_in_gitlab:
                self._sync_remote_mirror(mirror_in_gitlab)

        # Process enforcement: delete mirrors present in GitLab but not in config
        if enforce_mirrors:
            for gm in mirrors_in_gitlab:
                if gm.url not in mirrors_in_config:
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
            verbose(f"Failed to delete remote mirror '{mirror.url}'")

    def _sync_remote_mirror(self, mirror: ProjectRemoteMirror):
        """Trigger mirror.sync() when `force_push` is requested, with logging."""
        try:
            mirror.sync()
            verbose(f"Triggered sync for remote mirror '{mirror.url}'")
        except Exception:
            verbose(f"Failed to trigger sync for remote mirror '{mirror.url}'")
