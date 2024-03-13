from cli_ui import fatal, info

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.lists import OmissionReason, Groups


from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException
from gitlabform.gitlab.groups import GitLabGroups


class GroupsProvider:
    """
    For a query like "project/group", "group", "group/subgroup", ALL or ALL_DEFINED this
    class gets the effective lists of groups, taking into account skipped groups
    and the fact that the group and project names case are somewhat case-sensitive.
    """

    def __init__(self, gitlab, configuration):
        self.gitlab = gitlab
        self.configuration = configuration

    def get_groups(self, target: str) -> Groups:
        """
        :param target: "project/group", "group", "group/subgroup", ALL or ALL_DEFINED
        :return: Groups
        """

        if target not in ["ALL", "ALL_DEFINED"]:
            groups = self._get_single_group(target)
        else:
            groups = self._get_groups(target)

        return groups

    def _get_single_group(self, target: str) -> Groups:
        groups = Groups()

        # it may be a subgroup or a group...
        try:
            maybe_group = self.gitlab.get_group_case_insensitive(target)
            groups.add_requested([maybe_group["full_path"]])

        except NotFoundException:
            # ...or a single project, which we ignore here
            pass

        return groups

    def _get_groups(self, target: str) -> Groups:
        groups = Groups()

        if target == "ALL":
            groups.add_requested(self.gitlab.get_groups())
        else:  # ALL_DEFINED
            groups.add_requested(self.configuration.get_groups())

        groups.add_omitted(
            OmissionReason.SKIPPED, self._get_skipped_groups(groups.get_effective())
        )

        if target == "ALL_DEFINED":
            # check if all the groups from the config actually exist
            self._verify_if_groups_exist(groups.get_effective())

        return groups

    def _verify_if_groups_exist(self, groups: list):
        for group in groups:
            try:
                self.gitlab.get_group_case_insensitive(group)
            except NotFoundException:
                try:
                    self._create_group_if_needed(group)
                except Exception as e:
                    fatal(
                        f"Configuration contains group {group} but it cannot be found in GitLab nor could it be created! {e}",
                        exit_code=EXIT_INVALID_INPUT,
                    )

    def _create_group_if_needed(self, group: str):
        group_config = self.configuration.get_effective_config_for_group(group)
        if group_config.get("create_if_not_found", False):
            path_elements = group.split("/")
            parent_name, group_name = "/".join(path_elements[:-1]), path_elements[-1]
            parent_id = (
                self.gitlab.get_group_id_case_insensitive(parent_name)
                if parent_name != ""
                else None
            )
            self.gitlab.create_group(name=group_name, path=group_name, parent_id=parent_id)
        else:
            raise NotFoundException()

    def _get_skipped_groups(self, groups: list) -> list:
        skipped = []
        for group in groups:
            if self.configuration.is_group_skipped(group):
                skipped.append(group)

        return skipped
