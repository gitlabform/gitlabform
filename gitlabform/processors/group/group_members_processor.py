import sys
from typing import Dict, Tuple

from logging import debug, info, critical, error

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.gitlab import GitLab, AccessLevel
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab.v4.objects import Group, GroupMember, User
from gitlab import GitlabDeleteError, GitlabError


class GroupMembersProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_members", gitlab)

    def _process_configuration(self, group_name: str, configuration: dict):
        keep_bots = configuration.get("group_members|keep_bots", False)

        enforce_group_members = configuration.get("group_members|enforce", False)

        # We define that Group_Member users must be key-ed by Username rather than id e.g.:
        # group_members:
        #   users:
        #     user-name:

        (
            groups_to_set_by_group_path,
            usernames_in_config,
        ) = self._get_groups_and_users_from_config(configuration)

        if enforce_group_members and not groups_to_set_by_group_path and not usernames_in_config:
            critical(
                "Group members configuration section has to contain"
                " some 'users' or 'groups' defined as Owners,"
                " if you want to enforce them (GitLab requires it)."
            )
            sys.exit(EXIT_INVALID_INPUT)

        group = self.gl.get_group_by_path_cached(group_name)

        self._process_groups(group, groups_to_set_by_group_path, enforce_group_members)

        self._process_users(
            usernames_in_config,
            enforce_group_members,
            keep_bots,
            group,
        )

    @staticmethod
    def _get_groups_and_users_from_config(configuration: dict) -> Tuple[dict, dict]:
        groups_to_set_by_group_path = configuration.get("group_members|groups", {})

        users_in_config = configuration.get("group_members", {})
        if users_in_config:
            proper_users_to_set_by_username = configuration.get("group_members|users", {})
            if proper_users_to_set_by_username:
                return groups_to_set_by_group_path, proper_users_to_set_by_username

            users_in_config.pop("enforce", None)
            users_in_config.pop("users", None)
            users_in_config.pop("groups", None)
            users_in_config.pop("keep_bots", None)

        return groups_to_set_by_group_path, users_in_config

    def _process_groups(
        self,
        group_being_processed: Group,
        groups_to_share_with_by_path: dict,
        enforce_group_members: bool,
    ):
        shared_with_groups_before = group_being_processed.shared_with_groups
        info("Group shared with BEFORE: %s", shared_with_groups_before)

        groups_before_by_group_path = dict()
        for shared_with_group in shared_with_groups_before:
            groups_before_by_group_path[shared_with_group["group_full_path"]] = shared_with_group

        for share_with_group_path in groups_to_share_with_by_path:
            group_access_to_set = groups_to_share_with_by_path[share_with_group_path]["group_access"]

            expires_at_to_set = (
                groups_to_share_with_by_path[share_with_group_path]["expires_at"]
                if "expires_at" in groups_to_share_with_by_path[share_with_group_path]
                else None
            )

            if share_with_group_path in groups_before_by_group_path:
                group_access_before = groups_before_by_group_path[share_with_group_path]["group_access_level"]
                expires_at_before = groups_before_by_group_path[share_with_group_path]["expires_at"]

                if group_access_before == group_access_to_set and expires_at_before == expires_at_to_set:
                    info(
                        "Nothing to change for group '%s' - same config now as to set.",
                        share_with_group_path,
                    )
                else:
                    info(f"Re-adding group {share_with_group_path} to change their access level or expires at.")
                    share_with_group_id = groups_before_by_group_path[share_with_group_path]["group_id"]
                    # we will remove the group first and then re-add them,
                    # to ensure that the group has the expected access level
                    self._unshare(group_being_processed, share_with_group_id)

                    try:
                        group_being_processed.share(share_with_group_id, group_access_to_set, expires_at_to_set)
                    except GitlabError as e:
                        error(f"Error processing {share_with_group_path}, {e.error_message}")
                        raise e

            else:
                info(
                    f"Adding group {share_with_group_path} who previously was not a member.",
                )

                # group_id is pre-resolved by PrincipalIdsTransformer
                share_with_group_id = groups_to_share_with_by_path[share_with_group_path]["group_id"]
                try:
                    group_being_processed.share(share_with_group_id, group_access_to_set, expires_at_to_set)
                except GitlabError as e:
                    error(f"Error processing {share_with_group_path}, {e.error_message}")
                    raise e

        if enforce_group_members:
            # remove groups not configured explicitly
            groups_not_configured = set(groups_before_by_group_path) - set(groups_to_share_with_by_path)
            for group_path in groups_not_configured:
                info(
                    "Removing group '%s' who is not configured to be a member.",
                    group_path,
                )
                share_with_group_id = self.gl.get_group_id(group_path)
                self._unshare(group_being_processed, share_with_group_id)
        else:
            info("Not enforcing group members.")

        info(
            "Group shared with AFTER: %s",
            group_being_processed.members.list(get_all=True),
        )

    @staticmethod
    def _unshare(group_being_processed, share_with_group_id):
        try:
            group_being_processed.unshare(share_with_group_id)
        except GitlabDeleteError:
            info(f"Group with id {share_with_group_id} could not be unshared, likely was never shared to begin with")
            pass

    def _process_users(
        self,
        usernames_in_config: dict,
        enforce_group_members: bool,
        keep_bots: bool,
        group: Group,
    ):
        users_in_gitlab_by_lowercase_name = self.get_group_members_by_lowercase_name(group)

        info("Group members BEFORE: %s", users_in_gitlab_by_lowercase_name.keys())

        if usernames_in_config:
            # group users to set by access level
            users_to_set_by_access_level: Dict[int, list] = dict()
            for username in usernames_in_config:
                access_level = usernames_in_config[username]["access_level"]
                users_to_set_by_access_level.setdefault(access_level, []).append(username)

            # we HAVE TO start configuring access from the highest access level - in case of groups this is Owner
            # - to ensure that we won't end up with no Owner in a group
            for level in reversed(sorted(AccessLevel.group_levels())):
                users_to_set_with_this_level = (
                    users_to_set_by_access_level[level] if level in users_to_set_by_access_level else []
                )

                for username in users_to_set_with_this_level:
                    access_level_to_set = usernames_in_config[username]["access_level"]
                    expires_at_to_set = (
                        usernames_in_config[username]["expires_at"]
                        if "expires_at" in usernames_in_config[username]
                        else None
                    )

                    member_role_id_or_name = (
                        usernames_in_config[username]["member_role"]
                        if "member_role" in usernames_in_config[username]
                        else None
                    )
                    if member_role_id_or_name:
                        member_role_id_to_set = self.gl.get_member_role_id_cached(
                            member_role_id_or_name, group.full_path
                        )
                    else:
                        member_role_id_to_set = None

                    lower_case_username = username.lower()

                    # PrincipalIdsTransformer adds the user_id under the username key so we can get it from the config
                    # without needing to do an extra API call here
                    user_id = usernames_in_config[username]["user_id"]

                    if lower_case_username in users_in_gitlab_by_lowercase_name:
                        group_member: GroupMember = group.members.get(user_id)

                        user_in_gitlab = users_in_gitlab_by_lowercase_name[lower_case_username]
                        access_level_before = user_in_gitlab.access_level
                        expires_at_before = user_in_gitlab.expires_at
                        if hasattr(user_in_gitlab, "member_role"):
                            member_role_id_before = user_in_gitlab.member_role["id"]
                        else:
                            member_role_id_before = None

                        if (
                            access_level_before == access_level_to_set
                            and expires_at_before == expires_at_to_set
                            and member_role_id_before == member_role_id_to_set
                        ):
                            info(
                                "Nothing to change for user '%s' - same config now as to set.",
                                lower_case_username,
                            )
                        else:
                            info(
                                f"Editing user {lower_case_username} to change their access level to {access_level_to_set},"
                                f" expires at to {expires_at_to_set},"
                                f" and member_role_id to {member_role_id_to_set}."
                            )

                            group_member.access_level = access_level_to_set
                            group_member.expires_at = expires_at_to_set
                            group_member.member_role_id = member_role_id_to_set
                            try:
                                group_member.save()
                            except GitlabError as e:
                                error(f"Could not save user {lower_case_username}, error: {e.error_message}")
                                raise e

                    else:
                        info(f"Adding user {lower_case_username} who previously was not a member.")
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
            users_not_configured = set(users_in_gitlab_by_lowercase_name.keys()) - set(
                [username.lower() for username in usernames_in_config.keys()]
            )
            for username in users_not_configured:
                info(f"Removing user {username} who is not configured to be a member.")

                gl_user: User | None = self.gl.get_user_by_username_cached(username)

                if gl_user is None:
                    # User does not exist an instance level but is for whatever reason present on a Group/Project
                    # We should raise error into Logs but not prevent the rest of GitLabForm from executing
                    # This error is more likely to be prevalent in Dedicated instances; it is unlikely for a User to
                    # be completely deleted from gitlab.com
                    error(f"Could not find User '{username}' on the Instance so can not remove User from Group")
                    continue

                if keep_bots and gl_user.bot:
                    info(f"Will not remove bot user '{username}' as the 'keep_bots' option is true.")
                    continue

                try:
                    group.members.delete(gl_user.id)
                except GitlabDeleteError as delete_error:
                    error(f"Member '{username}' could not be deleted: {delete_error}")
                    raise delete_error

        else:
            info("Not enforcing group members.")

        info(f"Group members AFTER: {group.members.list(get_all=True)}")

    @staticmethod
    def get_group_members_by_lowercase_name(group) -> dict:
        members = group.members.list(get_all=True)
        users = {}
        for member in members:
            users[member.username.lower()] = member
        return users
