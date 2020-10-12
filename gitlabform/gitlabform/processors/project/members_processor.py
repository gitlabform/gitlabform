import logging

from gitlabform.gitlab import GitLab
from gitlabform.gitlabform.processors.abstract_processor import AbstractProcessor


class MembersProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("members")
        self.gitlab = gitlab

    def _process_configuration(self, project_and_group: str, configuration: dict):
        groups = configuration.get("members|groups")
        if groups:
            for group in groups:
                logging.debug("Setting group '%s' as a member", group)
                access = (
                    groups[group]["group_access"]
                    if "group_access" in groups[group]
                    else None
                )
                expiry = (
                    groups[group]["expires_at"] if "expires_at" in groups[group] else ""
                )

                # we will remove group access first and then re-add them,
                # to ensure that the groups have the expected access level
                self.gitlab.unshare_with_group(project_and_group, group)
                self.gitlab.share_with_group(project_and_group, group, access, expiry)

        users = configuration.get("members|users")
        if users:
            for user in users:
                logging.debug("Setting user '%s' as a member", user)
                access = (
                    users[user]["access_level"]
                    if "access_level" in users[user]
                    else None
                )
                expiry = (
                    users[user]["expires_at"] if "expires_at" in users[user] else ""
                )
                self.gitlab.remove_member_from_project(project_and_group, user)
                self.gitlab.add_member_to_project(
                    project_and_group, user, access, expiry
                )
