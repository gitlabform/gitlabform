from logging import debug

from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor
from gitlabform.processors.util.difference_logger import DifferenceLogger


class ProtectedEnvironmentsProcessor(MultipleEntitiesProcessor):
    """https://docs.gitlab.com/ee/api/protected_environments.html#protect-repository-environments"""

    def __init__(self, gitlab: GitLab):
        super().__init__(
            "protected_environments",
            gitlab,
            list_method_name=gitlab.list_protected_environments,
            add_method_name=gitlab.protect_a_repository_environment,
            delete_method_name=gitlab.unprotect_environment,
            defining=Key("name"),
            required_to_create_or_update=And(Key("name"), Key("deploy_access_levels")),
        )

        self.custom_diff_analyzers[
            "deploy_access_levels"
        ] = self._deploy_access_levels_delta_analyzer

    @staticmethod
    def _deploy_access_levels_delta_analyzer(
        cfg_key: str, cfg_in_gitlab: list, local_cfg: list
    ) -> bool:
        if len(cfg_in_gitlab) != len(local_cfg):
            return True

        for index in range(len(cfg_in_gitlab)):
            from_gitlab = {
                k: v for k, v in cfg_in_gitlab[index].items() if v is not None
            }
            from_local_cfg = local_cfg[index]

            keys_on_both_sides = set(from_gitlab.keys()) & set(from_local_cfg.keys())

            for key in keys_on_both_sides:
                if from_gitlab[key] != from_local_cfg[key]:
                    debug(
                        f"* A <{key}> in [{cfg_key}] differs: GitLab :: {from_gitlab} != Local :: {from_local_cfg}"
                    )
                    return True

        return False

    def _print_diff(self, project_or_project_and_group: str, entity_config: dict):
        # TODO: yeah... I didn't get how this is supposed to work :-(
        # Should I receive (from the super class) the "live" cfg from Gitlab ?
        DifferenceLogger.log_diff(
            f"Project {project_or_project_and_group} {self.configuration_name} changes",
            self.gitlab.list_protected_environments(project_or_project_and_group),
            entity_config,
        )
