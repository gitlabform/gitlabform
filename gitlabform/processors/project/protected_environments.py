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
            edit_method_name=gitlab.update_a_protected_environment,
            delete_method_name=gitlab.unprotect_environment,
            # TODO: I had to define "name" inside the cfg, it should get the section's name as the entity name, e.g.
            # protected_environments:
            #   foo:
            #     name: "foo" <- This is redundant
            #
            defining=Key("name"),
            required_to_create_or_update=And(Key("name"), Key("deploy_access_levels")),
        )

    def _print_diff(self, project_or_project_and_group: str, entity_config: dict):
        # TODO: yeah... I didn't get how this is supposed to work :-(
        # Should I receive (from the super class) the "live" cfg from Gitlab ?
        DifferenceLogger.log_diff(
            f"Project {project_or_project_and_group} {self.configuration_name} changes",
            self.gitlab.list_protected_environments(project_or_project_and_group),
            entity_config,
        )
