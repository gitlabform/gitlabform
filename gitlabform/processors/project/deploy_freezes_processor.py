from logging import debug

from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployFreezesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_freezes", gitlab)

    @staticmethod
    def _key(period: dict) -> tuple[str, str, str]:
        return period["freeze_start"].strip(), period["freeze_end"].strip(), period.get("cron_timezone") or "UTC"

    def _process_configuration(self, project_and_group: str, configuration: dict):
        debug("Processing deploy freezes...")
        section = configuration.get("deploy_freezes")
        periods = section.get("periods") if isinstance(section, dict) else None
        if not isinstance(periods, list):
            raise Exception("'deploy_freezes|periods' must be a list, use an empty list to delete all freeze periods")

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        path = f"/projects/{project.id}/freeze_periods"
        periods_in_gitlab = self.gl.http_list(path, get_all=True)
        keys_in_gitlab = {self._key(p) for p in periods_in_gitlab}
        keys_in_config = {self._key(p) for p in periods}

        for key in keys_in_config - keys_in_gitlab:
            debug(f"Creating deploy freeze {key}")
            freeze_start, freeze_end, cron_timezone = key
            self.gl.http_post(
                path,
                post_data={"freeze_start": freeze_start, "freeze_end": freeze_end, "cron_timezone": cron_timezone},
            )

        enforce = configuration.get("deploy_freezes|enforce")
        kept = set()
        for period in periods_in_gitlab:
            key = self._key(period)
            if key in keys_in_config and key not in kept:
                kept.add(key)
            elif key in keys_in_config:
                debug(f"Deleting duplicate deploy freeze {key}")
                self.gl.http_delete(f"{path}/{period['id']}")
            elif enforce:
                debug(f"Deleting deploy freeze {key}, it is not in the configuration and enforce is enabled")
                self.gl.http_delete(f"{path}/{period['id']}")
