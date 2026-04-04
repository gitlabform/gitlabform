from typing import Optional, Any

from cli_ui import info, warning, error, fatal, debug as verbose
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabOperationError,
)
from gitlab.v4.objects import Project, ProjectProtectedBranch

from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.strict = strict

        # Protected Branch API: https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
        # Behind the scenes gitlab will map "allowed_to_merge" and "merge_access_level" to "merge_access_levels"
        # and the same for unprotect and push access, so we need some custom diff analyzers to validate if the config
        # has actually changed
        self.custom_diff_analyzers["merge_access_levels"] = self.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["push_access_levels"] = self.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["unprotect_access_levels"] = self.naive_access_level_diff_analyzer

    def _can_proceed(self, project_or_group: str, configuration: dict):
        for branch in sorted(configuration["branches"]):
            branch_config = configuration["branches"][branch]
            if branch_config.get("protected") is None:
                fatal(f"The Protected key is mandatory in branches configuration, fix {branch} YAML config")

        return True

    def _process_configuration(self, project_and_group: str, configuration: dict):
        """
        Called from process defined in abstract_processor.py after checking self._can_proceed
        Processes the branches configuration
        """

        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for branch in sorted(configuration["branches"]):
            branch_configuration: dict = self.convert_user_and_group_names_to_ids(configuration["branches"][branch])

            self.process_branch_protection(project, branch, branch_configuration)

    def process_branch_protection(self, project: Project, branch_name: str, branch_config: dict):
        """
        Process branch protection according to gitlabform config.
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
                    fatal(
                        message,
                        exit_code=EXIT_INVALID_INPUT,
                    )
                else:
                    warning(message)

        try:
            protected_branch = project.protectedbranches.get(branch_name)
        except GitlabGetError:
            message = f"The branch '{branch_name}' is not protected!"
            verbose(message)

        if branch_config.get("protected"):
            if not protected_branch:
                verbose(f"Creating branch protection for {branch_name}")
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

            # We only build PATCH data for items requiring updates, e.g. if a merge_access_level has been changed or removed,
            # or if the code_owner_approval_required state has changed.
            # If we send everything the PATCH endpoint will return a 200 but not apply any updates.
            protected_branch_api_patch_data: dict = {}

            # Handle all top-level attributes generically to support raw parameter passing for updates
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
                        verbose(f"Creating data to update {key} as necessary")
                        protected_branch_api_patch_data[key] = value

            verbose("Creating data to update merge_access_levels as necessary")
            merge_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("merge_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "merge_access_levels")),
            )
            if len(merge_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_merge"] = merge_access_items_patch_data

            verbose("Creating data to update push_access_levels as necessary")
            push_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("push_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "push_access_levels")),
            )
            if len(push_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_push"] = push_access_items_patch_data

            verbose("Creating data to update unprotect_access_levels as necessary")

            unprotect_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("unprotect_access_levels"),
                existing_records=tuple(self._get_list_attribute(protected_branch, "unprotect_access_levels")),
            )

            if len(unprotect_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_unprotect"] = unprotect_access_items_patch_data

            if protected_branch_api_patch_data != {}:
                # We have some updates to make
                verbose(f"Updating protected branch {branch_name} with {protected_branch_api_patch_data}")
                self.protect_branch(project, branch_name, protected_branch_api_patch_data, True)

        elif protected_branch and not branch_config.get("protected"):
            verbose(f"Removing branch protection for {branch_name}")
            self.unprotect_branch(protected_branch)

    def process_branch_config_gitlab_under_15_6_0_or_ce(self, branch_config, branch_name, project, protected_branch):
        """
        Processes the branches configuration for gitlab version <=15.6.0 or Community Edition,
        first checking if the branch needs to be updated, if it does, then the branch will be unprotected prior to being
        reprotected with the YAML configuration.
        """

        # Gitlab returns the allowed_to_merge etc data in a different format from GET endpoint than it takes in
        # the POST (create) endpoint
        # GET: https://docs.gitlab.com/api/protected_branches/#get-a-single-protected-branch-or-wildcard-protected-branch
        # POST: https://docs.gitlab.com/api/protected_branches/#protect-repository-branches
        # Therefore we first transform the configured YAML into a state matching the gitlab GET endpoint,
        # before checking if it needs_update
        if self._needs_update(protected_branch.attributes, self.map_config_to_protected_branch_get_data(branch_config)):
            verbose(
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
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
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
                fatal(
                    message,
                    exit_code=EXIT_PROCESSING_ERROR,
                )
            else:
                warning(message)

    def convert_user_and_group_names_to_ids(self, branch_config: dict):
        """
        The branch configuration in gitlabform supports passing users or group using username
        or group name but GitLab only supports their id. This method will transform the
        config by replacing them with ids.
        """
        verbose("Transforming User and Group names in Branch configuration to Ids")

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
        """
        Branch protection CRUD API in python-gitlab (and GitLab itself) is
        inconsistent, the structure needed to create a branch protection rule is
        different from structure needed to update a rule in place.

        Also, "protected" attribute is missing from GitLab side of things.
        This method will normalize gitlabform branch_config to accommodate this.

        Args:
            our_branch_config (dict): branch configuration read from .yaml file

        Returns:
            dict: defined configuration transformed into the format returned by the Gitlab APIs
        """
        # Also see https://github.com/python-gitlab/python-gitlab/issues/2850

        verbose("Transforming *_access_level and allowed_to_* keys in Branch configuration")
        local_keys_to_gitlab_keys_map = {
            "merge_access_level": "merge_access_levels",
            "push_access_level": "push_access_levels",
            "unprotect_access_level": "unprotect_access_levels",
            "allowed_to_merge": "merge_access_levels",
            "allowed_to_push": "push_access_levels",
            "allowed_to_unprotect": "unprotect_access_levels",
        }
        new_branch_config = our_branch_config.copy()
        for key in our_branch_config:
            if key in local_keys_to_gitlab_keys_map.keys():
                target_key = local_keys_to_gitlab_keys_map[key]
                # *_access_level in gitlabform will have been transformed to it's int representation already if defined
                # by the user as "merge_access_level: Maintainer"
                if isinstance(our_branch_config[key], int):
                    access_level = new_branch_config.pop(key)
                    new_branch_config[target_key] = [
                        {
                            "id": None,
                            "access_level": access_level,
                            "user_id": None,
                            "group_id": None,
                            "deploy_key_id": None,
                        }
                    ]
                # allowed_to_* are lists...
                elif isinstance(our_branch_config[key], list):
                    mapped_list = []
                    for item in our_branch_config[key]:
                        # Raw Parameter Passing: Ensure comparison keys exist, but preserve everything else (like _destroy)
                        mapped_item = {
                            "id": None,
                            "access_level": item.get("access_level"),
                            "user_id": item.get("user_id"),
                            "group_id": item.get("group_id"),
                            "deploy_key_id": item.get("deploy_key_id"),
                            **{
                                k: v
                                for k, v in item.items()
                                if k not in ["access_level", "user_id", "group_id", "deploy_key_id", "id"]
                            },
                        }
                        mapped_list.append(mapped_item)
                    new_branch_config[target_key] = mapped_list
                    new_branch_config.pop(key)

        # this key is not present in
        # protected_branch.attributes, so _needs_update() would always
        # return True with this key present.
        new_branch_config.pop("protected")
        return new_branch_config

    @staticmethod
    def build_patch_request_data(transformed_access_levels: list[dict] | None, existing_records: tuple) -> list[dict]:
        """
        Compares the access_levels configuration (transformed to match the Gitlab GET response) to the existing access_level record in Gitlab.
        If there are no changes for a given access_level record an empty list is returned.
        Otherwise, data is returned to add/update access_level records and remove any outdated records.

        Gitlab supports merge_access_level for users with a Standard license and allowed_to_merge etc for users with Premium
        or Ultimate licenses.
        We need to support both options, and potentially blended configuration for users with Premium+ licenses.

        args:
            transformed_access_levels (list[dict|None]): transformed merge_access_levels or push_access_levels or unprotect_access_levels configration generated by transform_branch_config_access_levels
            existing_records (tuple): immutable list of existing records for the protected branch in Gitlab

        returns:
            list[dict]: Data in the format required by the protected_branches PATCH api. https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
        """
        patch_data = []

        if transformed_access_levels is not None:
            # User has defined in configuration some access level for this resource on the protected branch
            # Prepare patch data using raw parameters from config.
            # We only send non-None values and omit the internal 'id' placeholder used for mapping.
            for configuration in transformed_access_levels:
                item_to_add = {k: v for k, v in configuration.items() if v is not None and k != "id"}
                patch_data.append(item_to_add)

            # Check if we need to make the update (e.g. an existing record for that user_id or access_level exists)
            # and mark existing records for deletion if the access_level does not match
            # (e.g. config has changed from DEVELOPER to MAINTAINER; delete the DEVELOPER entry and add a MAINTAINER
            # entry)
            for existing_record in existing_records:
                existing_records_access_level = existing_record.get("access_level")
                existing_records_user_id = existing_record.get("user_id")
                existing_records_group_id = existing_record.get("group_id")
                existing_records_deploy_key_id = existing_record.get("deploy_key_id")

                is_match = False
                matching_item_in_patch = None

                for item in patch_data:
                    # We prioritize user_id and group_id matches over access_level.
                    # This avoids ambiguity because a user/group record from GitLab also contains an access_level.
                    # If we matched by access_level first, we might incorrectly pair a specific user's rule
                    # with a generic role-based rule from the config.
                    if existing_records_user_id is not None and item.get("user_id") == existing_records_user_id:
                        is_match = True
                    elif existing_records_group_id is not None and item.get("group_id") == existing_records_group_id:
                        is_match = True
                    elif (
                        existing_records_deploy_key_id is not None
                        and item.get("deploy_key_id") == existing_records_deploy_key_id
                    ):
                        is_match = True
                    elif (
                        item.get("user_id") is None
                        and item.get("group_id") is None
                        and item.get("deploy_key_id") is None
                    ):
                        # Role-based rule logic
                        local_level = item.get("access_level")
                        if local_level == existing_records_access_level:
                            is_match = True
                        elif local_level == 0 or existing_records_access_level == 0:
                            # "No Access" (0) is mutually exclusive with any other role.
                            # Mark existing for destruction so the new state can be applied.
                            record_id = existing_record.get("id")
                            patch_data.append({"id": record_id, "_destroy": True})
                            break

                    if is_match:
                        matching_item_in_patch = item
                        break

                if matching_item_in_patch:
                    # Rule already exists in GitLab, remove from the patch list to maintain idempotency
                    patch_data.remove(matching_item_in_patch)

                # Note: GitLabForm is additive by default. Explicit removal via user-provided _destroy is disabled
                # to preserve the core design principles.

        else:
            verbose("No configuration defined for this access level. No changes will be made.")

        return patch_data

    @staticmethod
    def naive_access_level_diff_analyzer(_, cfg_in_gitlab: list, local_cfg: list):
        """
        Determines if the branch protection rules need updating.
        Following GitLabForm's additive design, an update is needed if any rule
        defined in the local configuration is missing from GitLab.
        """
        # 1. Check if any local rule is missing from GitLab (Additive check)
        for local_item in local_cfg:
            found = False
            for gl_item in cfg_in_gitlab:
                # User Match
                if local_item.get("user_id") is not None:
                    if local_item.get("user_id") == gl_item.get("user_id"):
                        found = True
                        break
                # Group Match
                elif local_item.get("group_id") is not None:
                    if local_item.get("group_id") == gl_item.get("group_id"):
                        found = True
                        break
                # Deploy Key Match
                elif local_item.get("deploy_key_id") is not None:
                    if local_item.get("deploy_key_id") == gl_item.get("deploy_key_id"):
                        found = True
                        break
                # Role Match (Ensure GL item is also a role rule)
                if (
                    local_item.get("access_level") is not None
                    and local_item.get("access_level") == gl_item.get("access_level")
                    and gl_item.get("user_id") is None
                    and gl_item.get("group_id") is None
                    and gl_item.get("deploy_key_id") is None
                ):
                    found = True
                    break

            if not found:
                verbose("naive_access_level_diff_analyzer - needs_update: True (missing rule found)")
                return True

        # 2. Role exclusivity check (No Access handling)
        # Even if all local rules are "found", we need an update if GitLab has a "No Access" rule
        # while we want specific roles, or vice-versa.
        gl_role_levels = {
            r.get("access_level")
            for r in cfg_in_gitlab
            if r.get("user_id") is None and r.get("group_id") is None and r.get("deploy_key_id") is None
        }
        local_role_levels = {
            r.get("access_level")
            for r in local_cfg
            if r.get("user_id") is None and r.get("group_id") is None and r.get("deploy_key_id") is None
        }

        if (0 in gl_role_levels and any(lev > 0 for lev in local_role_levels)) or (
            0 in local_role_levels and any(lev > 0 for lev in gl_role_levels)
        ):
            verbose("naive_access_level_diff_analyzer - needs_update: True (No Access / Roles conflict)")
            return True

        verbose("naive_access_level_diff_analyzer - needs_update: False")
        return False

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
