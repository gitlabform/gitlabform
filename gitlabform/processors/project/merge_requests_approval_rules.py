from gitlab import GitlabGetError
from cli_ui import debug as verbose

from gitlabform.gitlab import GitLab
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class MergeRequestsApprovalRules(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "merge_requests_approval_rules",
            gitlab,
            list_method_name="get_approval_rules",
            add_method_name="add_approval_rule",
            edit_method_name="edit_approval_rule",
            delete_method_name="delete_approval_rule",
            defining=Key("name"),
            required_to_create_or_update=And(Key("name"), Key("approvals_required")),
        )

    def _process_configuration(self, project_or_group: str, configuration: dict):
        # Transform users -> user_ids and groups -> group_ids
        self._transform_approval_rule_identifiers(configuration)
        super()._process_configuration(project_or_group, configuration)

    def _transform_approval_rule_identifiers(self, configuration: dict):
        """
        Transform usernames to user_ids and group names to group_ids in approval rules.
        The GitLab API requires user_ids and group_ids, but for user-friendliness,
        the config allows specifying 'users' and 'groups' which are then transformed.
        """
        verbose("Transforming user and group names in merge_requests_approval_rules to IDs")

        rules = configuration.get(self.configuration_name, {})
        for rule_name, rule_config in rules.items():
            if rule_name == "enforce":  # Skip the enforce flag
                continue

            if isinstance(rule_config, dict):
                # Transform users -> user_ids
                if "users" in rule_config:
                    users = rule_config.pop("users")
                    user_ids = []
                    for username in users:
                        user_id = self.gl.get_user_id_cached(username)
                        if user_id is None:
                            raise GitlabGetError(
                                f"No users found when searching for username '{username}' "
                                f"in merge_requests_approval_rules config",
                                404,
                            )
                        user_ids.append(user_id)
                    rule_config["user_ids"] = user_ids

                # Transform groups -> group_ids
                if "groups" in rule_config:
                    groups = rule_config.pop("groups")
                    group_ids = []
                    for group_name in groups:
                        group_id = self.gl.get_group_id(group_name)
                        group_ids.append(group_id)
                    rule_config["group_ids"] = group_ids
