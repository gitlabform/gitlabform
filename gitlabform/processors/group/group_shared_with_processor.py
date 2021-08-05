import logging

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSharedWithProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_shared_with", gitlab)

    def _process_configuration(self, group: str, configuration: dict):
        groups_to_set_by_group_path = configuration.get("group_shared_with")
        if groups_to_set_by_group_path is None:
            groups_to_set_by_group_path = {}

        # group users before by group name
        groups_before = self.gitlab.get_group_case_insensitive(group)[
            "shared_with_groups"
        ]
        logging.debug("Group shared with BEFORE: %s", groups_before)

        groups_before_by_group_path = dict()
        for share_details in groups_before:
            groups_before_by_group_path[
                share_details["group_full_path"]
            ] = share_details

        for share_with_group_path in groups_to_set_by_group_path:

            group_access_to_set = groups_to_set_by_group_path[share_with_group_path][
                "group_access_level"
            ]

            expires_at_to_set = (
                groups_to_set_by_group_path[share_with_group_path]["expires_at"]
                if "expires_at" in groups_to_set_by_group_path[share_with_group_path]
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
                    logging.debug(
                        "Nothing to change for group '%s' - same config now as to set.",
                        share_with_group_path,
                    )
                else:
                    logging.debug(
                        "Re-adding group '%s' to change their access level or expires at.",
                        share_with_group_path,
                    )
                    # we will remove the group first and then re-add them,
                    # to ensure that the group has the expected access level
                    self.gitlab.remove_share_from_group(group, share_with_group_path)
                    self.gitlab.add_share_to_group(
                        group,
                        share_with_group_path,
                        group_access_to_set,
                        expires_at_to_set,
                    )

            else:
                logging.debug(
                    "Adding group '%s' who previously was not a member.",
                    share_with_group_path,
                )
                self.gitlab.add_share_to_group(
                    group, share_with_group_path, group_access_to_set, expires_at_to_set
                )

        if configuration.get("enforce_group_members"):
            # remove groups not configured explicitly
            groups_not_configured = set(groups_before_by_group_path) - set(
                groups_to_set_by_group_path
            )
            for group_path in groups_not_configured:
                logging.debug(
                    "Removing group '%s' who is not configured to be a member.",
                    group_path,
                )
                self.gitlab.remove_share_from_group(group, group_path)
        else:
            logging.debug("Not enforcing group members.")

        logging.debug(
            "Group shared with AFTER: %s", self.gitlab.get_group_members(group)
        )
