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

    def _needs_update(self, entity_in_gitlab: dict, entity_in_configuration: dict) -> bool:
        # GitLab returns users/groups as lists of objects and protected_branches as list
        # of objects with a "name" field, while the config (post-transform) has user_ids /
        # group_ids as int lists and protected_branches as list of names. Without
        # normalization the base _needs_update always triggers an update, even when nothing
        # changed. We normalize both sides unconditionally so keys line up regardless of
        # whether GitLab omitted an empty list or the user omitted the field in config.
        gitlab_norm = dict(entity_in_gitlab)
        gitlab_norm["user_ids"] = sorted(u["id"] for u in gitlab_norm.pop("users", []))
        gitlab_norm["group_ids"] = sorted(g["id"] for g in gitlab_norm.pop("groups", []))
        gitlab_norm["protected_branches"] = sorted(b["name"] for b in gitlab_norm.get("protected_branches", []))

        # edit_approval_rule treats missing user_ids/group_ids/protected_branches
        # in config as "clear them", so mirror that here to keep the comparison honest.
        config_norm = dict(entity_in_configuration)
        config_norm["user_ids"] = sorted(config_norm.get("user_ids", []))
        config_norm["group_ids"] = sorted(config_norm.get("group_ids", []))
        config_norm["protected_branches"] = sorted(config_norm.get("protected_branches", []))

        return super()._needs_update(gitlab_norm, config_norm)
