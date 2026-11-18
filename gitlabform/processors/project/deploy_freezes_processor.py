from logging import debug

from gitlab.v4.objects import Project

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class DeployFreezesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("deploy_freezes", gitlab)

    @staticmethod
    def _key(period: dict) -> tuple[str, str, str]:
        return period["freeze_start"], period["freeze_end"], period.get("cron_timezone") or "UTC"

    def _process_configuration(self, project_and_group: str, configuration: dict):
        debug("Processing deploy freezes...")
        project: Project = self.gl.get_project_by_path_cached(project_and_group)
        path = f"/projects/{project.id}/freeze_periods"
        periods_in_gitlab = {self._key(p): p for p in self.gl.http_list(path, get_all=True)}
        periods_in_config = {self._key(p): p for p in configuration.get("deploy_freezes|periods", [])}

        for key, period in periods_in_gitlab.items():
            if key not in periods_in_config:
                debug(f"Deleting deploy freeze {key}, it is not in the configuration")
                self.gl.http_delete(f"{path}/{period['id']}")

        for key, period in periods_in_config.items():
            if key in periods_in_gitlab:
                debug(f"Deploy freeze {key} remains unchanged")
            else:
                debug(f"Creating deploy freeze {key}")
                self.gl.http_post(path, post_data={"cron_timezone": "UTC", **period})
