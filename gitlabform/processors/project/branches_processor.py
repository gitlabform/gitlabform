import sys
from typing import Optional, Any

from logging import info, warning, error, critical
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabOperationError,
)
from gitlab.v4.objects import Project, ProjectProtectedBranch

from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.branch_protection import BranchProtection


class BranchesProcessor(AbstractProcessor):
    """
    Processor for branch protection settings.

    This processor is complex because GitLab's Protected Branches API uses different
    data structures for Create (POST), Get (GET), and Update (PATCH) operations.

    It implements 'Additive Design' (existing rules are preserved) and
    'Raw Parameter Passing' (arbitrary keys in config are sent to the API).
    """

    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.strict = strict

        # Protected Branch API: https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
        # Behind the scenes gitlab will map "allowed_to_merge" and "merge_access_level" to "merge_access_levels"
        # and the same for unprotect and push access, so we need some custom diff analyzers to validate if the config
        # has actually changed
        self.custom_diff_analyzers["merge_access_levels"] = BranchProtection.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["push_access_levels"] = BranchProtection.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["unprotect_access_levels"] = BranchProtection.naive_access_level_diff_analyzer

    def _can_proceed(self, project_or_group: str, configuration: dict):
        for branch in sorted(configuration["branches"]):
            branch_config = configuration["branches"][branch]
            if branch_config.get("protected") is None:
                critical(f"The Protected key is mandatory in branches configuration, fix {branch} YAML config")
                sys.exit(EXIT_INVALID_INPUT)

        return True

    def _process_configuration(self, project_and_group: str, configuration: dict):
        """
        Called from process defined in abstract_processor.py after checking self._can_proceed
        Iterates through all branches defined in the configuration and applies protection rules.
        """

        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for branch in sorted(configuration["branches"]):
            branch_configuration: dict = self.convert_user_and_group_names_to_ids(configuration["branches"][branch])

            self.process_branch_protection(project, branch, branch_configuration)

    def process_branch_protection(self, project: Project, branch_name: str, branch_config: dict):
        """
        High-level logic for processing branch protection.

        1. Validates branch existence (unless wildcard).
        2. Handles 'protected: false' (unprotecting).
        3. Handles 'protected: true':
           - If not currently protected: Create protection.
           - If protected: Update using PATCH (EE > 15.6) or Unprotect/Reprotect (CE/Old EE).
        """
        protected_branch: Optional[ProjectProtectedBranch] = None

        # If protected branch name contains a supported wildcard do not try looking it up
        if not self.branch_name_contains_supported_wildcard(branch_name):
            # Check branch we are trying to protect actually exists first
            try:
                project.branches.get(branch_name)
            except GitlabGetError:
                message = f"Branch '{branch_name}' not found when processing it to be protected/unprotected!"
                if self.strict:
                    critical(message)
                    sys.exit(EXIT_INVALID_INPUT)
                else:
                    warning(message)

        try:
            protected_branch = project.protectedbranches.get(branch_name)
        except GitlabGetError:
            message = f"The branch '{branch_name}' is not protected!"
            info(message)

        if branch_config.get("protected"):
            if not protected_branch:
                info(f"Creating branch protection for {branch_name}")
                self.protect_branch(project, branch_name, branch_config, False)
                return

            # https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch was only introduced after 15.6
            # for user's on older versions of Gitlab or Community Edition (https://gitlab.com/rluna-gitlab/gitlab-ce/-/work_items/37)
            # We need to unprotect and then reprotect the branch to apply the
            # defined configuration
            if self.gitlab.is_version_less_than("15.6.0") or (self.gitlab.enterprise == False):
                self.process_branch_config_gitlab_under_15_6_0_or_ce(
                    branch_config, branch_name, project, protected_branch
                )
                return

            # For later Gitlab versions we dynamically generate the data to send to the update endpoint based on the
            # configured state and the current Gitlab state so do not need to check _needs_update first.

            # Gitlab returns the allowed_to_merge etc. data in a different format from GET endpoint than it takes in
            # the POST (create) or PATCH (update) endpoints
            # GET: https://docs.gitlab.com/api/protected_branches/#get-a-single-protected-branch-or-wildcard-protected-branch
            # POST: https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
            # PATCH: https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
            # Therefore we first transform the configured YAML into a state matching the gitlab GET endpoint so we can
            # compare states easier to determine what PATCH request we need to send (if any)
            transformed_branch_config = self.map_config_to_protected_branch_get_data(branch_config)

            protected_branch_api_patch_data: dict = {}

            # RAW PARAMETER PASSING (Top-Level):
            # Iterate through any top-level flags (e.g., allow_force_push, code_owner_approval_required)
            # and include them in the PATCH request if they differ from the current GitLab state.
            special_list_keys = [
                "merge_access_levels",
                "push_access_levels",
                "unprotect_access_levels",
            ]
            for key, value in transformed_branch_config.items():
                if key not in special_list_keys:
                    # Check if this attribute exists on the GitLab object and needs an update
                    existing_value = getattr(protected_branch, key, None)
                    if existing_value != value:
                        info(f"Creating data to update {key} as necessary")
                        protected_branch_api_patch_data[key] = value

            info("Creating data to update merge_access_levels as necessary")
            merge_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("merge_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "merge_access_levels")),
            )
            if len(merge_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_merge"] = merge_access_items_patch_data

            info("Creating data to update push_access_levels as necessary")
            push_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("push_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "push_access_levels")),
            )
            if len(push_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_push"] = push_access_items_patch_data

            info("Creating data to update unprotect_access_levels as necessary")

            unprotect_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("unprotect_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "unprotect_access_levels")),
            )

            if len(unprotect_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_unprotect"] = unprotect_access_items_patch_data

            if protected_branch_api_patch_data != {}:
                # We have some updates to make
                info(f"Updating protected branch {branch_name} with {protected_branch_api_patch_data}")
                self.protect_branch(project, branch_name, protected_branch_api_patch_data, True)

        elif protected_branch and not branch_config.get("protected"):
            info(f"Removing branch protection for {branch_name}")
            self.unprotect_branch(protected_branch)

    def process_branch_config_gitlab_under_15_6_0_or_ce(self, branch_config, branch_name, project, protected_branch):
        """
        Processes the branches configuration for gitlab version <=15.6.0 or Community Edition,
        where in-place updates (PATCH) are not supported or effective.
        If a change is detected, the branch is unprotected and then reprotected from scratch.
        """

        # Gitlab returns the allowed_to_merge etc data in a different format from GET endpoint than it takes in
        # the POST (create) endpoint
        # GET: https://docs.gitlab.com/api/protected_branches/#get-a-single-protected-branch-or-wildcard-protected-branch
        # POST: https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
        # Therefore we first transform the configured YAML into a state matching the gitlab GET endpoint,
        # before checking if it needs_update
        if self._needs_update(protected_branch.attributes, self.map_config_to_protected_branch_get_data(branch_config)):
            info(
                f"Gitlab version is less than 15.6.0, so un-protecting and reprotecting branch {branch_name} to apply new config..."
            )
            self.unprotect_branch(protected_branch)

            # Send the untransformed config to the POST endpoint, as GitlabForm YAML structure conforms to the POST inputs
            self.protect_branch(project, branch_name, branch_config, False)

    def protect_branch(self, project: Project, branch_name: str, branch_config: dict, update_only: bool = False):
        """
        Create or update branch protection using given config.
        Raise exception if running in strict mode.

        args:
            project (Project): Gitlab project
            branch_name (str): Name of branch on the project to protect or update protection on
            branch_config (dict): Branch protection configuration to apply
            update_only (bool):
                If True, update branch protection of branch with branch_name,
                If False create a new protected branch with branch_name
        """
        try:
            if update_only:
                project.protectedbranches.update(branch_name, branch_config)
            else:
                project.protectedbranches.create({"name": branch_name, **branch_config})
        except GitlabOperationError as e:
            message = f"Protecting branch '{branch_name}' failed! Error '{e.error_message}"

            if self.strict:
                critical(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                error(message)

    def unprotect_branch(self, protected_branch: ProjectProtectedBranch):
        """
        Unprotect a branch.
        Raise exception if running in strict mode.
        """
        try:
            # The delete method doesn't delete the actual branch.
            # It only unprotects the branch.
            protected_branch.delete()
        except GitlabDeleteError as e:
            message = f"Branch '{protected_branch.name}' could not be unprotected! Error '{e.error_message}'"
            if self.strict:
                critical(message)
                sys.exit(EXIT_PROCESSING_ERROR)
            else:
                warning(message)

    def convert_user_and_group_names_to_ids(self, branch_config: dict):
        """
        Pre-processor to resolve names to IDs.
        Translates 'user: username' or 'group: name' into 'user_id' or 'group_id' as
        config by replacing them with ids.
        """
        info("Transforming User and Group names in Branch configuration to Ids")

        for key in branch_config:
            if isinstance(branch_config[key], list):
                for item in branch_config[key]:
                    if isinstance(item, dict):
                        if "user" in item:
                            username = item.pop("user")
                            user_id = self.gl.get_user_id_cached(username)
                            if user_id is None:
                                raise GitlabGetError(
                                    f"transform_branch_config - No users found when searching for username {username}",
                                    404,
                                )
                            item["user_id"] = user_id
                        elif "group" in item:
                            item["group_id"] = self.gl.get_group_id(item.pop("group"))

        return branch_config

    @staticmethod
    def map_config_to_protected_branch_get_data(our_branch_config: dict):
        return BranchProtection.map_config_to_protected_branch_get_data(our_branch_config)

    @staticmethod
    def build_patch_request_data(transformed_access_levels: list[dict] | None, existing_records: tuple) -> list[dict]:
        return BranchProtection.build_patch_request_data(transformed_access_levels, existing_records)

    @staticmethod
    def naive_access_level_diff_analyzer(_, cfg_in_gitlab: list, local_cfg: list):
        return BranchProtection.naive_access_level_diff_analyzer(_, cfg_in_gitlab, local_cfg)

    @staticmethod
    def branch_name_contains_supported_wildcard(branch):
        """
        Gitlab supports "*" wildcards when protecting branches:
        https://docs.gitlab.com/user/project/repository/branches/protected/#use-wildcard-rules
        """
        return "*" in branch

    @staticmethod
    def _get_list_attribute(protected_branch: ProjectProtectedBranch, attribute_name: str) -> list[Any]:
        """
        Gets list attribute such as unprotect_access_levels, merge_access_levels, push_access_levels, etc.
        Uses the python-gitlab attributes raw dict rather than direct parameter to gracefully handle when an attribute
        is not present in the API response.
        For example in CE: unprotect_access_levels is not returned on the protected_branch, so trying to access directly
        throws a runtime-exception
        """
        existing_list_value: list[Any] = []
        # Get from the "attributes" as this is the raw dict
        existing_attr = protected_branch.attributes.get(attribute_name)
        if existing_attr is not None:
            existing_list_value = existing_attr
        return existing_list_value
