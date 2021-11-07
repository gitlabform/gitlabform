from logging import debug, warning
from cli_ui import fatal

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab, AccessLevel
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupMembersProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_members", gitlab)

    def _process_configuration(self, group: str, configuration: dict):
        users_to_set_by_username = configuration.get("group_members")
        if users_to_set_by_username:

            # group users before by username
            users_before = self.gitlab.get_group_members(group)
            debug("Group members BEFORE: %s", users_before)
            users_before_by_username = dict()
            for user in users_before:
                users_before_by_username[user["username"]] = user

            # group users to set by access level
            users_to_set_by_access_level = dict()
            for user in users_to_set_by_username:
                access_level = users_to_set_by_username[user]["access_level"]
                users_to_set_by_access_level.setdefault(access_level, []).append(user)

            # check if the configured users contain at least one Owner
            if (
                AccessLevel.OWNER.value not in users_to_set_by_access_level.keys()
                and configuration.get("enforce_group_members")
            ):
                warning(
                    "With 'enforce_group_members' you need to have at least 1 Owner per group"
                    " (another group or a user). This is a GitLab's internal requirement."
                )

            # we HAVE TO start configuring access from the highest access level - in case of groups this is Owner
            # - to prevent a case when there is no Owner in a group
            for level in reversed(sorted(AccessLevel.group_levels())):

                users_to_set_with_this_level = (
                    users_to_set_by_access_level[level]
                    if level in users_to_set_by_access_level
                    else []
                )

                for user in users_to_set_with_this_level:

                    access_level_to_set = users_to_set_by_username[user]["access_level"]
                    expires_at_to_set = (
                        users_to_set_by_username[user]["expires_at"]
                        if "expires_at" in users_to_set_by_username[user]
                        else None
                    )

                    if user in users_before_by_username:

                        access_level_before = users_before_by_username[user][
                            "access_level"
                        ]
                        expires_at_before = users_before_by_username[user]["expires_at"]

                        if (
                            access_level_before == access_level_to_set
                            and expires_at_before == expires_at_to_set
                        ):
                            debug(
                                "Nothing to change for user '%s' - same config now as to set.",
                                user,
                            )
                        else:
                            debug(
                                "Re-adding user '%s' to change their access level or expires at.",
                                user,
                            )
                            # we will remove the user first and then re-add they,
                            # to ensure that the user has the expected access level
                            self.gitlab.remove_member_from_group(group, user)
                            self.gitlab.add_member_to_group(
                                group, user, access_level_to_set, expires_at_to_set
                            )

                    else:
                        debug("Adding user '%s' who previously was not a member.", user)
                        self.gitlab.add_member_to_group(
                            group, user, access_level_to_set, expires_at_to_set
                        )

            if configuration.get("enforce_group_members"):
                # remove users not configured explicitly
                # note: only direct members are removed - inherited are left
                users_not_configured = set(
                    [user["username"] for user in users_before]
                ) - set(users_to_set_by_username.keys())
                for user in users_not_configured:
                    debug(
                        "Removing user '%s' who is not configured to be a member.", user
                    )
                    self.gitlab.remove_member_from_group(group, user)
            else:
                debug("Not enforcing group members.")

            debug("Group members AFTER: %s", self.gitlab.get_group_members(group))

        else:

            fatal(
                "You cannot configure a group to have no members. GitLab requires a group "
                " to contain at least 1 member who is an Owner (access_level = 50).",
                exit_code=EXIT_INVALID_INPUT,
            )
