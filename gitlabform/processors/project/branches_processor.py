from typing import Optional
from cli_ui import info, warning, error, fatal, debug as verbose
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabOperationError,
)
from gitlab.v4.objects import Project, ProjectProtectedBranch

from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab, AccessLevel
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
                info(f"Creating branch protection for {branch_name}")
                self.protect_branch(project, branch_name, branch_config, False)
                return

            # https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch was only introduced after 15.6
            # for user's on older versions of Gitlab we need to unprotect and then reprotect the branch to apply the
            # defined configuration
            if self.gitlab.is_version_less_than("15.6.0"):
                self.process_branch_config_gitlab_15_6_0_or_older(branch_config, branch_name, project, protected_branch)
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

            verbose("Creating data to update code_owner_approval_required as necessary")
            code_owner_approval_required_patch_data = None
            code_owner_approval_required_config = transformed_branch_config.get("code_owner_approval_required")
            if (
                code_owner_approval_required_config is not None
                and protected_branch.code_owner_approval_required != code_owner_approval_required_config
            ):
                code_owner_approval_required_patch_data = transformed_branch_config.get("code_owner_approval_required")

            verbose("Creating data to update allow_force_push as necessary")
            allow_force_push_patch_data = None
            allow_force_push_config = transformed_branch_config.get("allow_force_push")
            if allow_force_push_config is not None and protected_branch.allow_force_push != allow_force_push_config:
                allow_force_push_patch_data = allow_force_push_config

            verbose("Creating data to update merge_access_levels as necessary")
            merge_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("merge_access_levels"),
                existing_records=tuple(protected_branch.merge_access_levels),
            )

            verbose("Creating data to update push_access_levels as necessary")
            push_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("push_access_levels"),
                existing_records=tuple(protected_branch.push_access_levels),
            )

            verbose("Creating data to update unprotect_access_levels as necessary")
            unprotect_access_items_patch_data = self.build_patch_request_data(
                transformed_access_levels=transformed_branch_config.get("unprotect_access_levels"),
                existing_records=tuple(protected_branch.unprotect_access_levels),
            )

            # We only build PATCH data for items requiring updates, e.g. if a merge_access_level has been changed or removed,
            # or if the code_owner_approval_required state has changed.
            # If we send everything the PATCH endpoint will return a 200 but not apply any updates.
            protected_branch_api_patch_data: dict = {}

            if len(merge_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_merge"] = merge_access_items_patch_data

            if len(push_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_push"] = push_access_items_patch_data

            if len(unprotect_access_items_patch_data) > 0:
                protected_branch_api_patch_data["allowed_to_unprotect"] = unprotect_access_items_patch_data

            if code_owner_approval_required_patch_data is not None:
                protected_branch_api_patch_data["code_owner_approval_required"] = (
                    code_owner_approval_required_patch_data
                )

            if allow_force_push_patch_data is not None:
                protected_branch_api_patch_data["allow_force_push"] = allow_force_push_patch_data

            if protected_branch_api_patch_data != {}:
                # We have some updates to make
                info(f"Updating protected branch {branch_name} with {protected_branch_api_patch_data}")
                self.protect_branch(project, branch_name, protected_branch_api_patch_data, True)

        elif protected_branch and not branch_config.get("protected"):
            info(f"Removing branch protection for {branch_name}")
            self.unprotect_branch(protected_branch)

    def process_branch_config_gitlab_15_6_0_or_older(self, branch_config, branch_name, project, protected_branch):
        """
        Processes the branches configuration for gitlab version 15.6.0 or older,
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
                            user_id = self.gl.get_user_id_cached(item.pop("user"))
                            if user_id is None:
                                raise GitlabGetError(
                                    f"transform_branch_config - No users found when searching for username {item.pop("user")}",
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
                # *_access_level in gitlabform will have been transformed to it's int representation already if defined
                # by the user as "merge_access_level: Maintainer"
                if isinstance(our_branch_config[key], int):
                    access_level = new_branch_config.pop(key)
                    new_branch_config[local_keys_to_gitlab_keys_map[key]] = [
                        {"id": None, "access_level": access_level, "user_id": None, "group_id": None}
                    ]
                # allowed_to_* are lists...
                elif isinstance(our_branch_config[key], list):
                    new_branch_config[local_keys_to_gitlab_keys_map[key]] = []
                    for item in our_branch_config[key]:
                        if "access_level" in item:
                            new_branch_config[local_keys_to_gitlab_keys_map[key]].append(
                                {"id": None, "access_level": item["access_level"], "user_id": None, "group_id": None}
                            )
                        elif "group_id" in item:
                            new_branch_config[local_keys_to_gitlab_keys_map[key]].append(
                                {"id": None, "access_level": None, "user_id": None, "group_id": item["group_id"]}
                            )
                        elif "user_id" in item:
                            new_branch_config[local_keys_to_gitlab_keys_map[key]].append(
                                {"id": None, "access_level": None, "user_id": item["user_id"], "group_id": None}
                            )
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
            for configuration in transformed_access_levels:
                configured_access_level = configuration.get("access_level")
                configured_user_id = configuration.get("user_id")
                configured_group_id = configuration.get("group_id")

                if configured_access_level is not None:
                    # Entry to configure an access level e.g.
                    # push_access_level: Maintainer
                    #
                    # or:
                    # allowed_to_push:
                    #   - access_level: Maintainer

                    # Create a new record for the new Access Level required
                    patch_data.append(
                        {
                            "access_level": configured_access_level,
                        }
                    )
                elif configured_user_id is not None:
                    # Entry to configure a user to have access, only available for users with "Premium" or "Ultimate" e.g.
                    # allowed_to_push:
                    #   - user: tim-knight
                    patch_data.append(
                        {
                            "user_id": configured_user_id,
                        }
                    )
                else:
                    # Entry to configure a group to have access, only available for users with "Premium" or "Ultimate" e.g.
                    # allowed_to_push:
                    #   - group_id: 15
                    patch_data.append(
                        {
                            "group_id": configured_group_id,
                        }
                    )

            # Mark records for deletion
            BranchesProcessor.add_patch_data_to_remove_existing_records(existing_records, patch_data)

            return patch_data
        else:
            verbose("No configuration defined for this access level, defaulting to Maintainer")
            # User has not defined either x_access_level OR allowed_to_x in their configuration
            # We should follow Gitlab convention and ensure the protected branch is set to Maintainer access level
            access_level_value = AccessLevel.MAINTAINER.value

            # Create a new record for the new Access Level required and mark the existing records for deletion
            patch_data.append(
                {
                    "access_level": access_level_value,
                }
            )

            # Mark records for deletion
            BranchesProcessor.add_patch_data_to_remove_existing_records(existing_records, patch_data)

            return patch_data

    @staticmethod
    def add_patch_data_to_remove_existing_records(existing_records: tuple, patch_data: list) -> None:
        """
        Adds data in the pattern defined in the gitlab api: https://docs.gitlab.com/api/protected_branches/#example-delete-a-push_access_level-record
        to the patch_data list

        If gitlab contains an "access_level" entry for one we are trying to configure, don't mark for deletion
            and re-creation, as we will likely get a "Merge Access Level access level already exists" error
            as well as it being relatively pointless data change

        args:
            existing_records (tuple|list): list of records from Gitlab from the protected_branch access_levels attributes (e.g. protected_branch.push_access_levels)
            patch_data (list): list of patch_data built from the configured YAML

        """
        for record_to_delete in existing_records:
            access_level = record_to_delete.get("access_level")
            matching_item_to_be_created = None

            if access_level is not None:
                # Gitlab entry is an "access_level" entry, find if we have configured one with the same level
                for item in patch_data:
                    if item.get("access_level") == access_level:
                        matching_item_to_be_created = item

            if matching_item_to_be_created is not None:
                # If we found an existing "access_level" item matching one that has been configured, remove the item
                # to be created and don't mark the existing record for deletion
                patch_data.remove(matching_item_to_be_created)
            else:
                record_id = record_to_delete.get("id")
                patch_data.append({"id": record_id, "_destroy": True})

    @staticmethod
    def naive_access_level_diff_analyzer(_, cfg_in_gitlab: list, local_cfg: list):

        if len(cfg_in_gitlab) != len(local_cfg):
            return True

        # GitLab UI, API, python-gitlab and GitLabForm itself make it impossible
        # to set "access_level", "user_id" and/or "group_id" at the same time,
        # so we take a naive approach here and kind of expect it will always be
        # either one of those, but not a combination
        needs_update = False
        changes_found = 0
        for item in local_cfg:
            if item["access_level"] and item["access_level"] >= 0:
                access_level = item["access_level"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["access_level"] != access_level:
                        changes_found += 1
            elif item["user_id"] and item["user_id"] >= 0:
                user_id = item["user_id"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["user_id"] != user_id:
                        changes_found += 1
            elif item["group_id"] and item["group_id"] >= 0:
                group_id = item["group_id"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["group_id"] != group_id:
                        changes_found += 1
        if changes_found > 0:
            needs_update = True
        verbose(f"naive_access_level_diff_analyzer - needs_update: {needs_update}, changes_found: {changes_found}")
        return needs_update

    @staticmethod
    def branch_name_contains_supported_wildcard(branch):
        """
        Gitlab supports "*" wildcards when protecting branches:
        https://docs.gitlab.com/user/project/repository/branches/protected/#use-wildcard-rules
        """
        return "*" in branch
