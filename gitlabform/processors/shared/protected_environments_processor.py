from gitlab import GitlabGetError
from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


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

        self.custom_diff_analyzers["deploy_access_levels"] = self.recursive_diff_analyzer

    def _process_configuration(self, project_or_group: str, configuration: dict):
        # Transform user -> user_id and group -> group_id in deploy_access_levels
        self._transform_deploy_access_levels(configuration)
        super()._process_configuration(project_or_group, configuration)

    def _transform_deploy_access_levels(self, configuration: dict):
        """
        Transform username to user_id and group name to group_id in deploy_access_levels.
        The GitLab API requires user_id and group_id, but for user-friendliness,
        the config allows specifying 'user' and 'group' which are then transformed.
        """
        verbose("Transforming user and group names in protected_environments deploy_access_levels to IDs")

        environments = configuration.get(self.configuration_name, {})
        for env_name, env_config in environments.items():
            if env_name == "enforce":  # Skip the enforce flag
                continue

            if "deploy_access_levels" in env_config:
                for access_level in env_config["deploy_access_levels"]:
                    if isinstance(access_level, dict):
                        if "user" in access_level:
                            username = access_level.pop("user")
                            user_id = self.gl.get_user_id_cached(username)
                            if user_id is None:
                                raise GitlabGetError(
                                    f"No users found when searching for username '{username}' "
                                    f"in protected_environments config",
                                    404,
                                )
                            access_level["user_id"] = user_id
                        elif "group" in access_level:
                            group_name = access_level.pop("group")
                            group_id = self.gl.get_group_id(group_name)
                            access_level["group_id"] = group_id
