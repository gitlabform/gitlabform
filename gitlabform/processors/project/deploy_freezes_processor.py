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
        if not isinstance(section, dict) or not isinstance(section.get("periods"), list):
            raise Exception("'deploy_freezes|periods' must be a list")

        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        path = f"/projects/{project.id}/freeze_periods"
        enforce = section.get("enforce", False)
        keys_in_config = {self._key(p) for p in section["periods"]}

        kept = set()
        to_delete = []
        for period in self.gl.http_list(path, get_all=True):
            key = self._key(period)
            if key in keys_in_config and key not in kept:
                kept.add(key)
            elif key in keys_in_config or enforce:
                to_delete.append((key, period["id"]))

        for key in keys_in_config - kept:
            debug(f"Creating deploy freeze {key}")
            freeze_start, freeze_end, cron_timezone = key
            self.gl.http_post(
                path,
                post_data={"freeze_start": freeze_start, "freeze_end": freeze_end, "cron_timezone": cron_timezone},
            )

        for key, period_id in to_delete:
            debug(f"Deleting deploy freeze {key}, it is a duplicate or not in the configuration with enforce enabled")
            self.gl.http_delete(f"{path}/{period_id}")
