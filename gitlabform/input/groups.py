from cli_ui import fatal

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.input.core import Groups, Projects, OmissionReason

# from gitlabform.gitlab.core import NotFoundException


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

        except Exception:  # TODO: this should be NotFoundException but it causes an import issue
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
            except Exception:  # TODO: this should be NotFoundException but it causes an import issue
                fatal(
                    f"Configuration contains group {group} but it cannot be found in GitLab!",
                    exit_code=EXIT_INVALID_INPUT,
                )

    def _get_skipped_groups(self, groups: list) -> list:
        skipped = []
        for group in groups:
            if self.configuration.is_group_skipped(group):
                skipped.append(group)

        return skipped
