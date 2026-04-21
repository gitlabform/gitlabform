import sys
from typing import Optional, Any

from logging import info, warning, error, critical, debug
from gitlab import GitlabGetError, GitlabDeleteError, GitlabOperationError
from gitlab.v4.objects.branches import GroupProtectedBranch
from gitlab.v4.objects.groups import Group

from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.branch_protection import BranchProtection


class GroupBranchesProcessor(AbstractProcessor):

    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("group_branches", gitlab)
        self.strict = strict

        self.custom_diff_analyzers["merge_access_levels"] = BranchProtection.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["push_access_levels"] = BranchProtection.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["unprotect_access_levels"] = BranchProtection.naive_access_level_diff_analyzer

    def _can_proceed(self, group: str, configuration: dict):
        for branch in sorted(configuration["group_branches"]):
            branch_config = configuration["group_branches"][branch]
            if branch_config.get("protected") is None:
                critical(f"The Protected key is mandatory in group_branches configuration, fix {branch} YAML config")
                sys.exit(EXIT_INVALID_INPUT)

        return True

    def _process_configuration(self, group: str, configuration: dict):
        gitlab_group: Group = self.gl.get_group_by_path_cached(group)

        for branch in sorted(configuration["group_branches"]):
            branch_configuration: dict = configuration["group_branches"][branch]

            self.process_branch_protection(gitlab_group, branch, branch_configuration)

    def process_branch_protection(self, group: Group, branch_name: str, branch_config: dict):
        protected_branch: Optional[GroupProtectedBranch] = None

        try:
            protected_branch = group.protectedbranches.get(branch_name)
        except GitlabGetError:
            debug(f"The branch '{branch_name}' is not protected at group level!")

        if branch_config.get("protected"):
            if not protected_branch:
                info(f"Creating group-level branch protection for {branch_name}")
                self.protect_branch(group, branch_name, branch_config, False)
                return

            transformed_branch_config = BranchProtection.map_config_to_protected_branch_get_data(branch_config)

            protected_branch_api_patch_data: dict = {}

            special_list_keys = [
                "merge_access_levels",
                "push_access_levels",
                "unprotect_access_levels",
            ]
            for key, value in transformed_branch_config.items():
                if key not in special_list_keys:
                    existing_value = getattr(protected_branch, key, None)
                    if existing_value != value:
                        debug(f"Creating data to update {key} as necessary")
                        protected_branch_api_patch_data[key] = value

            debug("Creating data to update merge_access_levels as necessary")
            merge_access_items_patch_data = BranchProtection.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("merge_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "merge_access_levels")),
            )
            if len(merge_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_merge"] = merge_access_items_patch_data

            debug("Creating data to update push_access_levels as necessary")
            push_access_items_patch_data = BranchProtection.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("push_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "push_access_levels")),
            )
            if len(push_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_push"] = push_access_items_patch_data

            debug("Creating data to update unprotect_access_levels as necessary")
            unprotect_access_items_patch_data = BranchProtection.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("unprotect_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "unprotect_access_levels")),
            )
            if len(unprotect_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_unprotect"] = unprotect_access_items_patch_data

            if protected_branch_api_patch_data != {}:
                info(f"Updating group-level protected branch {branch_name} with {protected_branch_api_patch_data}")
                self.protect_branch(group, branch_name, protected_branch_api_patch_data, True)

        elif protected_branch and not branch_config.get("protected"):
            info(f"Removing group-level branch protection for {branch_name}")
            self.unprotect_branch(protected_branch)

    def protect_branch(self, group: Group, branch_name: str, branch_config: dict, update_only: bool = False):
        try:
            if update_only:
                group.protectedbranches.update(branch_name, branch_config)
            else:
                group.protectedbranches.create({"name": branch_name, **branch_config})
        except GitlabOperationError as e:
            message = f"Protecting branch '{branch_name}' at group level failed! Error '{e.error_message}"

            if self.strict:
                critical(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                error(message)

    def unprotect_branch(self, protected_branch: GroupProtectedBranch):
        try:
            protected_branch.delete()
        except GitlabDeleteError as e:
            message = (
                f"Branch '{protected_branch.name}' could not be unprotected at group level! Error '{e.error_message}'"
            )
            if self.strict:
                critical(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                warning(message)

    @staticmethod
    def _get_list_attribute(protected_branch: GroupProtectedBranch, attribute_name: str) -> list[Any]:
        existing_list_value: list[Any] = []
        existing_attr = protected_branch.attributes.get(attribute_name)
        if existing_attr is not None:
            existing_list_value = existing_attr
        return existing_list_value
