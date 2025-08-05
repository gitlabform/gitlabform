from typing import Optional
from cli_ui import warning, fatal, debug as verbose
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabOperationError,
)
from gitlab.v4.objects import Project, ProjectProtectedBranch

from gitlabform import gitlab
from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab, AccessLevel
from gitlabform.processors.abstract_processor import AbstractProcessor


#### File level methods which do not require class variables, allowing for easier unit testing ####


def _map_allowed_to_config_to_access_levels(config: list[dict]):
    """
    Converts config defined in Gitlabform for "allowed_to_merge", "allowed_to_push", "allowed_to_unprotect" into
    items which can be passed to the PATCH api for Create/Update operations

    For updating/creating user_id and group_id entries we must also pass access_level, which Gitlab defaults
    to Maintainer

    - https://docs.gitlab.com/api/protected_branches/#example-update-a-push_access_level-record
    - https://docs.gitlab.com/api/protected_branches/#example-create-a-push_access_level-record
    """
    output = []
    for item in config:
        if item.get("access_level") is not None:
            value = item.get("access_level")
            access_level_value = get_access_level_value(value)
            mapped_item = {
                "access_level": access_level_value,
            }
        elif item.get("user_id") is not None:
            value = item.get("user_id")
            mapped_item = {
                "user_id": value,
            }
        elif item.get("group_id") is not None:
            value = item.get("group_id")
            mapped_item = {
                "group_id": value,
            }
        else:
            continue
        output.append(mapped_item)

    return output


def get_access_level_value(value: int | str):
    """
    Given an AccessLevel defined either as an integer or as a string, return the value as an integer.

    For example, an input of "Maintainer" returns 40

    Args:
        value (int|str): the AccessLevel
    """
    if isinstance(value, str):
        access_level_value = AccessLevel.get_value(value)
    else:
        access_level_value = value
    return access_level_value


def append_records_for_deletion(access_items: list, records_to_delete: list | tuple):
    """
    Appends information to the access_items list in order to mark records for deletion.
    Creates data in the pattern defined in the gitlab api: https://docs.gitlab.com/api/protected_branches/#example-delete-a-push_access_level-record

    Args:
        access_items (list): List of items to be passed to the Gitlab protected_branches PATCH api in order to modify the access_levels of the branch
        records_to_delete (list): List of records from Gitlab from the protected_branch access_levels attributes (e.g. protected_branch.push_access_levels), which will be marked for destruction
    """
    for record in records_to_delete:
        record_id = record.get("id")
        access_items.append({"id": record_id, "_destroy": True})


def find_config_matching_existing_record(configured_items_to_create: list[dict], record: dict, key: str):
    """
    Given an existing record from Gitlab, finds a matching item defined in the config.
    Match is performed on the key passed in, e.g. matches on user_id or group_id

    Args:
        configured_items_to_create (list[dict]): list items defined in configuration
        record (dict): a given record from Gitlab from the protected_branch access_levels attributes (e.g. protected_branch.push_access_levels)
        key (str): key to match on, e.g. group_id, user_id, access_level
    """
    matching_config = next(
        (item for item in configured_items_to_create if item.get(key) is not None and item.get(key) == record.get(key)),
        None,
    )
    return matching_config


def build_patch_request_data(
    allowed_to_config: list[dict] | None, level_config: str | None, existing_records: tuple[dict]
) -> list[dict]:
    """
    Given the "allowed_to_x" and "x_access_level" configuration defined in Gitlabform, and the existing_records for that
    access level in Gitlab. Build a dictionary of data to pass to the update() endpoint in Gitlab

    Gitlab supports merge_access_level for users with a Standard license and allowed_to_merge etc for users with Premium
    or Ultimate licenses.
    We need to support both options, and potentially blended configuration for users with Premium+ licenses.

    args:
        allowed_to_config (list[dict|None]): allowed_to_merge or allowed_to_push or allowed_to_unprotect config defined in Gitlabform
        level_config (str): merge_access_level or push_access_level or unprotect_access_level config defined in Gitlabform
        existing_records (tuple[dict]): immutable list of existing records

    returns:
        list[dict]: Data in the format required by the protected_branches PATCH api. https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
    """
    access_items_to_patch = []
    if level_config is None:
        # e.g.: User has not defined "merge_access_level" in config
        if allowed_to_config is None:
            # e.g.: User has also not defined "allowed_to_merge" rules in config
            access_level_value = AccessLevel.MAINTAINER.value

            if len(existing_records) == 1:
                # User has previously defined only "x_access_level" in config there will only be one record in Gitlab
                record = existing_records[0]
                # Record already has access level defined, so no updates to make
                if record.get("access_level") == access_level_value:
                    return []

            # Create a new record for the new Access Level required and mark the existing records for deletion
            access_items_to_patch.append(
                {
                    "access_level": access_level_value,
                }
            )

            append_records_for_deletion(access_items=access_items_to_patch, records_to_delete=existing_records)
        else:
            # e.g.: User has defined allowed_to_merge rules
            configured_items_to_create = _map_allowed_to_config_to_access_levels(allowed_to_config)

            for record in existing_records:
                if record.get("user_id") is not None:
                    # Record is a User allowed to merge record, do we have one for this user already?
                    matching_config = find_config_matching_existing_record(
                        configured_items_to_create, record, "user_id"
                    )
                    if matching_config is not None:
                        # Do not delete existing Record and no need to create one either
                        configured_items_to_create.remove(matching_config)
                        continue
                elif record.get("group_id") is not None:
                    # Record is a Group allowed to merge record, do we have one for this group already?
                    matching_config = find_config_matching_existing_record(
                        configured_items_to_create, record, "group_id"
                    )
                    if matching_config is not None:
                        # Do not delete existing Record and no need to create one either
                        configured_items_to_create.remove(matching_config)
                        continue
                elif record.get("access_level") is not None:
                    # Record is a pure Access Level record, do we have one in config with the same Access Level
                    matching_config = find_config_matching_existing_record(
                        configured_items_to_create, record, "access_level"
                    )
                    if matching_config is not None:
                        # Do not delete existing Record, no need to create a new one, but we do need to pass
                        # the existing one back to the PATCH api
                        configured_items_to_create.remove(matching_config)
                        access_items_to_patch.append(
                            {
                                "id": record.get("id"),
                                "access_level": record.get("access_level"),
                                "_update": True,
                            }
                        )
                        continue

                # No matching item found in config, so add record for deletion
                access_items_to_patch.append({"id": record.get("id"), "_destroy": True})

            for item in configured_items_to_create:
                # When creating user_id or group_id entry we must also provide access_level, defaulted to Maintainer
                # as per https://docs.gitlab.com/api/protected_branches/#update-a-protected-branch
                if item.get("access_level") is None:
                    access_items_to_patch.append(
                        {
                            **item,
                            "access_level": AccessLevel.MAINTAINER.value,
                        }
                    )
                else:
                    access_items_to_patch.append(item)
    else:
        # e.g.: User has defined "merge_access_level" in config

        access_level_value = get_access_level_value(level_config)
        if len(existing_records) == 1:
            # User has previously defined only "x_access_level" in config there will only be one record in Gitlab
            record = existing_records[0]
            # Record already has access level defined, so no updates to make
            if record.get("access_level") == access_level_value:
                return []

        # Create a new record for the new Access Level required and mark the existing records for deletion
        access_items_to_patch.append(
            {
                "access_level": access_level_value,
            }
        )

        append_records_for_deletion(access_items=access_items_to_patch, records_to_delete=existing_records)

    return access_items_to_patch


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

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for branch in sorted(configuration["branches"]):
            branch_configuration: dict = self.convert_user_and_group_names_to_ids(configuration["branches"][branch])

            self.process_branch_protection(project, branch, branch_configuration)

    def process_branch_protection(self, project: Project, branch_name: str, branch_config: dict):
        """
        Process branch protection according to gitlabform config.
        """
        protected_branch: Optional[ProjectProtectedBranch] = None

        if not self.is_branch_name_wildcard(branch_name):
            try:
                branch = project.branches.get(branch_name)
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
            if protected_branch:
                # Branch matching this name exists, so check for updates

                # Transform the config from "allowed_to_push" or "push_access_level" into "push_access_levels" array to
                # match how the data is stored in the Gitlab backend
                branch_config_for_needs_update = self.transform_branch_config_access_levels(branch_config)
                if self._needs_update(protected_branch.attributes, branch_config_for_needs_update):
                    # For GitLab version < 15.6 - need to unprotect the branch
                    # and then re-protect again using current config
                    verbose("Updating branch protection for ':%s'", branch_name)
                    if not self.gitlab.is_version_at_least("15.6.0"):
                        self.unprotect_branch(protected_branch)
                        self.protect_branch(project, branch_name, branch_config, False)
                    else:
                        if self.set_code_owner_approval_required(
                            branch_config, protected_branch
                        ) or self.set_allow_force_push(branch_config, protected_branch):
                            # No need to call the API if we haven't had to change either of "allow_force_push" or
                            # "code_owner_approval_required"
                            protected_branch.save()

                        merge_access_items = build_patch_request_data(
                            allowed_to_config=branch_config.get("allowed_to_merge"),
                            level_config=branch_config.get("merge_access_level"),
                            existing_records=tuple(protected_branch.merge_access_levels),
                        )

                        push_access_items = build_patch_request_data(
                            allowed_to_config=branch_config.get("allowed_to_push"),
                            level_config=branch_config.get("push_access_level"),
                            existing_records=tuple(protected_branch.push_access_levels),
                        )

                        unprotect_access_items = build_patch_request_data(
                            allowed_to_config=branch_config.get("allowed_to_unprotect"),
                            level_config=branch_config.get("unprotect_access_level"),
                            existing_records=tuple(protected_branch.unprotect_access_levels),
                        )

                        branch_config_prepared_for_update = {}

                        if len(merge_access_items) > 0:
                            branch_config_prepared_for_update["allowed_to_merge"] = merge_access_items

                        if len(push_access_items) > 0:
                            branch_config_prepared_for_update["allowed_to_push"] = push_access_items

                        if len(unprotect_access_items) > 0:
                            branch_config_prepared_for_update["allowed_to_unprotect"] = unprotect_access_items

                        if branch_config_prepared_for_update != {}:
                            # We have some updates to Access Levels to make
                            self.protect_branch(project, branch_name, branch_config_prepared_for_update, True)
            elif not protected_branch:
                verbose("Creating branch protection for ':%s'", branch_name)
                self.protect_branch(project, branch_name, branch_config, False)
        elif protected_branch and not branch_config.get("protected"):
            verbose("Removing branch protection for ':%s'", branch_name)
            self.unprotect_branch(protected_branch)

    def protect_branch(self, project: Project, branch_name: str, branch_config: dict, update_only: bool):
        """
        Create or update branch protection using given config.
        Raise exception if running in strict mode.
        """
        verbose("Setting branch '%s' as protected", branch_name)
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
                warning(message)

    def unprotect_branch(self, protected_branch: ProjectProtectedBranch):
        """
        Unprotect a branch.
        Raise exception if running in strict mode.
        """

        verbose("Setting branch '%s' as unprotected", protected_branch.name)

        try:
            # The delete method doesn't delete the actual branch.
            # It only unprotects the branch.
            protected_branch.delete()
        except GitlabDeleteError as e:
            message = f"Branch '{protected_branch.name}' could not be unprotected! Error '{e.error_message}"
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
    def set_code_owner_approval_required(branch_config: dict, protected_branch: ProjectProtectedBranch):
        """
        Sets the state of code_owner_approval_required on the protected branch.
        If code_owner_approval_required is not set in the gitlabform config we assume it should not be required
        e.g. set to False

        Returns:
              bool: whether a change was made to the protected_branch attribute
        """
        configured_state = branch_config.get("code_owner_approval_required")
        branch_state = protected_branch.code_owner_approval_required

        if configured_state is None and branch_state:
            protected_branch.code_owner_approval_required = False
            return True
        elif configured_state is not None and branch_state != configured_state:
            protected_branch.code_owner_approval_required = configured_state
            return True

        return False

    @staticmethod
    def set_allow_force_push(branch_config: dict, protected_branch: ProjectProtectedBranch):
        """
        Sets the state of allow_force_push on the protected branch.
        If allow_force_push is not set in the gitlabform config we assume it should not be required
        e.g. set to False

        Returns:
              bool: whether a change was made to the protected_branch attribute
        """
        configured_state = branch_config.get("allow_force_push")
        branch_state = protected_branch.allow_force_push

        if configured_state is None and branch_state:
            protected_branch.allow_force_push = False
            return True
        elif configured_state is not None and branch_state != configured_state:
            protected_branch.allow_force_push = configured_state
            return True

        return False

    @staticmethod
    def transform_branch_config_access_levels(our_branch_config: dict):
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
                # *_access_level in gitlabform is of type int
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
    def is_branch_name_wildcard(branch):
        return "*" in branch or "?" in branch
