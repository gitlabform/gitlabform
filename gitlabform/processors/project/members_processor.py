from logging import debug
from cli_ui import debug as verbose
from cli_ui import fatal

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class MembersProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("members", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):

        enforce_members = configuration.get("members|enforce", False)

        groups = configuration.get("members|groups", {})

        users = configuration.get("members|users", {})

        if not groups and not users and not enforce_members:
            fatal(
                "Project members configuration section has to contain"
                " either 'users' or 'groups' non-empty keys"
                " (unless you want to enforce no direct members).",
                exit_code=EXIT_INVALID_INPUT,
            )

        self._process_groups(project_and_group, groups, enforce_members)
        self._process_users(project_and_group, users, enforce_members)

    def _process_groups(
        self, project_and_group: str, groups: dict, enforce_members: bool
    ):
        if groups:

            verbose("Processing groups as members...")

            current_groups = self.gitlab.get_groups_from_project(project_and_group)
            for group in groups:
                expires_at = (
                    groups[group]["expires_at"].strftime("%Y-%m-%d")
                    if "expires_at" in groups[group]
                    else None
                )
                access_level = (
                    groups[group]["group_access"]
                    if "group_access" in groups[group]
                    else None
                )

                # we only add the group if it doesn't have the correct settings
                if (
                    group in current_groups
                    and expires_at == current_groups[group]["expires_at"]
                    and access_level == current_groups[group]["group_access_level"]
                ):
                    debug("Ignoring group '%s' as it is already a member", group)
                    debug(
                        "Current settings for '%s' are: %s"
                        % (group, current_groups[group])
                    )
                else:
                    debug("Setting group '%s' as a member", group)
                    access = access_level
                    expiry = expires_at

                    # we will remove group access first and then re-add them,
                    # to ensure that the groups have the expected access level
                    self.gitlab.unshare_with_group(project_and_group, group)
                    self.gitlab.share_with_group(
                        project_and_group, group, access, expiry
                    )

        if enforce_members:

            current_groups = self.gitlab.get_groups_from_project(project_and_group)

            groups_in_config = groups.keys()
            groups_in_gitlab = current_groups.keys()
            groups_not_in_config = set(groups_in_gitlab) - set(groups_in_config)

            for group_not_in_config in groups_not_in_config:
                debug(
                    f"Removing group '{group_not_in_config}' that is not configured to be a member."
                )
                self.gitlab.unshare_with_group(project_and_group, group_not_in_config)
        else:
            debug("Not enforcing group members.")

    def _process_users(
        self, project_and_group: str, users: dict, enforce_members: bool
    ):
        if users:

            verbose("Processing users as members...")

            current_members = self.gitlab.get_members_from_project(project_and_group)
            for user in users:
                expires_at = (
                    users[user]["expires_at"].strftime("%Y-%m-%d")
                    if "expires_at" in users[user]
                    else None
                )
                access_level = (
                    users[user]["access_level"]
                    if "access_level" in users[user]
                    else None
                )
                # we only add the user if it doesn't have the correct settings
                if (
                    user in current_members
                    and expires_at == current_members[user]["expires_at"]
                    and access_level == current_members[user]["access_level"]
                ):
                    debug("Ignoring user '%s' as it is already a member", user)
                    debug(
                        "Current settings for '%s' are: %s"
                        % (user, current_members[user])
                    )
                else:
                    debug("Setting user '%s' as a member", user)
                    access = access_level
                    expiry = expires_at
                    self.gitlab.remove_member_from_project(project_and_group, user)
                    self.gitlab.add_member_to_project(
                        project_and_group, user, access, expiry
                    )

        if enforce_members:

            current_members = self.gitlab.get_members_from_project(project_and_group)

            users_in_config = users.keys()
            users_in_gitlab = current_members.keys()
            users_not_in_config = set(users_in_gitlab) - set(users_in_config)

            for user_not_in_config in users_not_in_config:
                debug(
                    f"Removing user '{user_not_in_config}' that is not configured to be a member."
                )
                self.gitlab.remove_member_from_project(
                    project_and_group, user_not_in_config
                )
        else:
            debug("Not enforcing user members.")
