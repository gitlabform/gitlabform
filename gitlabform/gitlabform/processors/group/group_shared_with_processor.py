import logging
import sys

import cli_ui

from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform import EXIT_INVALID_INPUT
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class GroupSharedWithProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_shared_with")
        self.gitlab = gitlab

    def _process_configuration(self, group: str, configuration: dict):
        groups_to_set_by_groupname = configuration.get("group_shared_with")
        if groups_to_set_by_groupname is None:
            groups_to_set_by_groupname = {}

        # group users before by group name
        groups_before = self.gitlab.get_group_case_insensitive(group)[
            "shared_with_groups"
        ]
        logging.debug("Group shared with BEFORE: %s", groups_before)
        groups_before_by_group_id = dict()
        for share_details in groups_before:
            groups_before_by_group_id[share_details["group_id"]] = share_details

        groups_to_set_by_group_id = set()

        for groupname in groups_to_set_by_groupname:

            try:
                group_id = self.gitlab.get_group_case_insensitive(groupname)["id"]
            except NotFoundException:
                cli_ui.error(f"Group {groupname} not found.")
                sys.exit(EXIT_INVALID_INPUT)

            groups_to_set_by_group_id.add(group_id)

            group_access_to_set = groups_to_set_by_groupname[groupname][
                "group_access_level"
            ]

            expires_at_to_set = (
                groups_to_set_by_groupname[groupname]["expires_at"]
                if "expires_at" in groups_to_set_by_groupname[groupname]
                else None
            )

            if group_id in groups_before_by_group_id:

                group_access_before = groups_before_by_group_id[group_id][
                    "group_access_level"
                ]
                expires_at_before = groups_before_by_group_id[group_id]["expires_at"]

                if (
                    group_access_before == group_access_to_set
                    and expires_at_before == expires_at_to_set
                ):
                    logging.debug(
                        "Nothing to change for group '%s' - same config now as to set.",
                        groupname,
                    )
                else:
                    logging.debug(
                        "Re-adding group '%s' to change their access level or expires at.",
                        groupname,
                    )
                    # we will remove the group first and then re-add them,
                    # to ensure that the group has the expected access level
                    self.gitlab.remove_share_from_group(group, group_id)
                    self.gitlab.add_share_to_group(
                        group, group_id, group_access_to_set, expires_at_to_set
                    )

            else:
                logging.debug(
                    "Adding group '%s' who previously was not a member.", groupname
                )
                self.gitlab.add_share_to_group(
                    group, group_id, group_access_to_set, expires_at_to_set
                )

        if configuration.get("enforce_group_members"):
            # remove groups not configured explicitly
            groups_not_configured = (
                set(groups_before_by_group_id) - groups_to_set_by_group_id
            )
            for group_id in groups_not_configured:
                logging.debug(
                    "Removing group '%s' who is not configured to be a member.",
                    group_id,
                )
                self.gitlab.remove_share_from_group(group, group_id)
        else:
            logging.debug("Not enforcing group members.")

        logging.debug(
            "Group shared with AFTER: %s", self.gitlab.get_group_members(group)
        )
