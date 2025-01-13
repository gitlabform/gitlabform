from logging import debug, warning
from typing import Dict, Tuple

import gitlab
from cli_ui import fatal, error, debug as verbose

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab, AccessLevel
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab.v4.objects import Group, GroupMember
from gitlab import GitlabDeleteError, GitlabGetError


class GroupMembersProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_members", gitlab)

    def _process_configuration(self, group_name: str, configuration: dict):
        keep_bots = configuration.get("group_members|keep_bots", False)

        enforce_group_members = configuration.get("group_members|enforce", False)

        (
            groups_to_set_by_group_path,
            users_to_set_by_username,
        ) = self._get_groups_and_users_to_set(configuration)

        if (
            enforce_group_members
            and not groups_to_set_by_group_path
            and not users_to_set_by_username
        ):
            fatal(
                "Group members configuration section has to contain"
                " some 'users' or 'groups' defined as Owners,"
                " if you want to enforce them (GitLab requires it).",
                exit_code=EXIT_INVALID_INPUT,
            )

        group = self.gl.get_group_by_path_cached(group_name)

        self._process_groups(group, groups_to_set_by_group_path, enforce_group_members)

        self._process_users(
            users_to_set_by_username,
            enforce_group_members,
            keep_bots,
            group,
        )

    @staticmethod
    def _get_groups_and_users_to_set(configuration: dict) -> Tuple[dict, dict]:
        groups_to_set_by_group_path = configuration.get("group_members|groups", {})

        users_to_set_by_username = configuration.get("group_members", {})
        if users_to_set_by_username:
            proper_users_to_set_by_username = configuration.get(
                "group_members|users", {}
            )
            if proper_users_to_set_by_username:
                users_to_set_by_username = proper_users_to_set_by_username
            else:
                users_to_set_by_username.pop("enforce", None)
                users_to_set_by_username.pop("users", None)
                users_to_set_by_username.pop("groups", None)
                users_to_set_by_username.pop("keep_bots", None)

        return groups_to_set_by_group_path, users_to_set_by_username

    def _process_groups(
        self,
        group_being_processed: Group,
        groups_to_share_with_by_path: dict,
        enforce_group_members: bool,
    ):
        shared_with_groups_before = group_being_processed.shared_with_groups
        debug("Group shared with BEFORE: %s", shared_with_groups_before)

        groups_before_by_group_path = dict()
        for shared_with_group in shared_with_groups_before:
            groups_before_by_group_path[shared_with_group["group_full_path"]] = (
                shared_with_group
            )

        for share_with_group_path in groups_to_share_with_by_path:
            group_access_to_set = groups_to_share_with_by_path[share_with_group_path][
                "group_access"
            ]

            expires_at_to_set = (
                groups_to_share_with_by_path[share_with_group_path]["expires_at"]
                if "expires_at" in groups_to_share_with_by_path[share_with_group_path]
                else None
            )

            if share_with_group_path in groups_before_by_group_path:
                group_access_before = groups_before_by_group_path[
                    share_with_group_path
                ]["group_access_level"]
                expires_at_before = groups_before_by_group_path[share_with_group_path][
                    "expires_at"
                ]

                if (
                    group_access_before == group_access_to_set
                    and expires_at_before == expires_at_to_set
                ):
                    debug(
                        "Nothing to change for group '%s' - same config now as to set.",
                        share_with_group_path,
                    )
                else:
                    debug(
                        "Re-adding group '%s' to change their access level or expires at.",
                        share_with_group_path,
                    )
                    share_with_group_id = groups_before_by_group_path[
                        share_with_group_path
                    ]["group_id"]
                    # we will remove the group first and then re-add them,
                    # to ensure that the group has the expected access level
                    self._unshare(group_being_processed, share_with_group_id)

                    group_being_processed.share(
                        share_with_group_id, group_access_to_set, expires_at_to_set
                    )

            else:
                debug(
                    "Adding group '%s' who previously was not a member.",
                    share_with_group_path,
                )

                share_with_group_id = self.gl.get_group_id(share_with_group_path)
                group_being_processed.share(
                    share_with_group_id, group_access_to_set, expires_at_to_set
                )

        if enforce_group_members:
            # remove groups not configured explicitly
            groups_not_configured = set(groups_before_by_group_path) - set(
                groups_to_share_with_by_path
            )
            for group_path in groups_not_configured:
                debug(
                    "Removing group '%s' who is not configured to be a member.",
                    group_path,
                )
                share_with_group_id = self.gl.get_group_id(group_path)
                self._unshare(group_being_processed, share_with_group_id)
        else:
            debug("Not enforcing group members.")

        debug(
            "Group shared with AFTER: %s",
            group_being_processed.members.list(get_all=True),
        )

    @staticmethod
    def _unshare(group_being_processed, share_with_group_id):
        try:
            group_being_processed.unshare(share_with_group_id)
        except GitlabDeleteError:
            debug("Group could not be unshared, likely was never shared to begin with")
            pass

    def _process_users(
        self,
        users_to_set_by_username: dict,
        enforce_group_members: bool,
        keep_bots: bool,
        group: Group,
    ):
        # group users before by username
        # (note: we DON'T get inherited users as we don't manage them at this level anyway)
        users_before = self.get_group_members(group)

        debug("Group members BEFORE: %s", users_before.keys())

        if users_to_set_by_username:
            # group users to set by access level
            users_to_set_by_access_level: Dict[int, list] = dict()
            for user in users_to_set_by_username:
                access_level = users_to_set_by_username[user]["access_level"]
                users_to_set_by_access_level.setdefault(access_level, []).append(user)

            # we HAVE TO start configuring access from the highest access level - in case of groups this is Owner
            # - to ensure that we won't end up with no Owner in a group
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

                    member_role_id_or_name = (
                        users_to_set_by_username[user]["member_role"]
                        if "member_role" in users_to_set_by_username[user]
                        else None
                    )
                    if member_role_id_or_name:
                        member_role_id_to_set = self.gl.get_member_role_id_cached(
                            member_role_id_or_name, group.full_path
                        )
                    else:
                        member_role_id_to_set = None

                    common_username = user.lower()
                    try:
                        user_id = self.gl.get_user_id_cached(user)
                    except gitlab.GitlabGetError as e:
                        error(
                            f"Could not find User '{user}' on the Instance so can not configure User defined in Config"
                        )
                        raise e

                    if common_username in users_before:
                        group_member: GroupMember = group.members.get(user_id)

                        user_before = users_before[common_username]
                        access_level_before = user_before.access_level
                        expires_at_before = user_before.expires_at
                        if hasattr(user_before, "member_role"):
                            member_role_id_before = user_before.member_role["id"]
                        else:
                            member_role_id_before = None

                        if (
                            access_level_before == access_level_to_set
                            and expires_at_before == expires_at_to_set
                            and member_role_id_before == member_role_id_to_set
                        ):
                            debug(
                                "Nothing to change for user '%s' - same config now as to set.",
                                common_username,
                            )
                        else:
                            debug(
                                "Editing user '%s' membership to change their access level or expires at.",
                                common_username,
                            )

                            group_member.access_level = access_level_to_set
                            group_member.expires_at = expires_at_to_set
                            group_member.member_role_id = member_role_id_to_set
                            group_member.save()

                    else:
                        debug(
                            "Adding user '%s' who previously was not a member.",
                            common_username,
                        )
                        group.members.create(
                            {
                                "user_id": user_id,
                                "access_level": access_level_to_set,
                                "expires_at": expires_at_to_set,
                                "member_role_id": member_role_id_to_set,
                            }
                        )

        if enforce_group_members:
            # remove users not configured explicitly
            # note: only direct members are removed - inherited are left
            users_not_configured = set(users_before.keys()) - set(
                [username.lower() for username in users_to_set_by_username.keys()]
            )
            for user in users_not_configured:
                if keep_bots and self.gitlab.get_user_by_name(user)["bot"]:
                    debug(
                        f"Will not remove bot user '{user}' as the 'keep_bots' option is true."
                    )
                    continue
                verbose(f"Removing user {user} who is not configured to be a member.")
                try:
                    user_id = self.gl.get_user_id_cached(user)
                except GitlabGetError:
                    # User does not exist an instance level but is for whatever reason present on a Group/Project
                    # We should raise error into Logs but not prevent the rest of GitLabForm from executing
                    # This error is more likely to be prevalent in Dedicated instances; it is unlikely for a User to
                    # be completely deleted from gitlab.com
                    error(
                        f"Could not find User '{user}' on the Instance so can not remove User"
                    )
                    continue

                try:
                    group.members.delete(user_id)
                except GitlabDeleteError as delete_error:
                    error(f"Member '{user}' could not be deleted: {delete_error}")
                    raise delete_error

        else:
            debug("Not enforcing group members.")

        debug(f"Group members AFTER: {group.members.list(get_all=True)}")

    @staticmethod
    def get_group_members(group) -> dict:
        members = group.members.list(get_all=True)
        users = {}
        for member in members:
            users[member.username.lower()] = member
        return users
