from logging import debug
from typing import Optional
from cli_ui import warning, fatal, debug as verbose
from gitlab import (
    GitlabGetError,
    GitlabDeleteError,
    GitlabCreateError,
)
from gitlab.v4.objects import Project, ProjectProtectedBranch

from gitlabform import gitlab
from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class BranchesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("branches", gitlab)
        self.strict = strict
        self.custom_diff_analyzers["merge_access_levels"] = self.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["push_access_levels"] = self.naive_access_level_diff_analyzer
        self.custom_diff_analyzers["unprotect_access_levels"] = self.naive_access_level_diff_analyzer

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project: Project = self.gl.get_project_by_path_cached(project_and_group)

        for branch in sorted(configuration["branches"]):
            branch_configuration: dict = self.transform_branch_config(configuration["branches"][branch])

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
            debug(message)

        if branch_config.get("protected"):
            if protected_branch:
                branch_config_for_needs_update = self.transform_branch_config_access_levels(
                    branch_config, protected_branch.attributes
                )
                if self._needs_update(protected_branch.attributes, branch_config_for_needs_update):
                    # For GitLab version < 15.6 - need to unprotect the branch
                    # and then re-protect again using current config
                    debug("Updating branch protection for ':%s'", branch_name)
                    if self.gitlab_version < (15, 6):
                        self.unprotect_branch(protected_branch)
                        self.protect_branch(project, branch_name, branch_config, False)
                    else:
                        branch_config_prepared_for_update = self.prepare_branch_config_for_update(
                            branch_config, protected_branch
                        )
                        self.protect_branch(project, branch_name, branch_config_prepared_for_update, True)
            elif not protected_branch:
                debug("Creating branch protection for ':%s'", branch_name)
                self.protect_branch(project, branch_name, branch_config, False)
        elif protected_branch and not branch_config.get("protected"):
            debug("Removing branch protection for ':%s'", branch_name)
            self.unprotect_branch(protected_branch)

    def protect_branch(self, project: Project, branch_name: str, branch_config: dict, update_only: bool):
        """
        Create or update branch protection using given config.
        Raise exception if running in strict mode.
        """

        try:
            if update_only:
                project.protectedbranches.update(branch_name, branch_config)
            else:
                project.protectedbranches.create({"name": branch_name, **branch_config})
        except GitlabCreateError as e:
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

        debug("Setting branch '%s' as unprotected", protected_branch.name)

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

    def prepare_branch_config_for_update(self, our_branch_config: dict, gitlab_branch_config: ProjectProtectedBranch):
        """Prepare GitLabForm branch config for "update" operation.

        This function also removes branch protection access rules that not defined in GitLabForm config.

        Args:
            our_branch_config (dict): branch configuration read from .yaml file
            gitlab_branch_config (ProjectProtectedBranch): branch configuration obtained from GitLab

        Returns:
            dict: copy of our_branch_config updated with needed metadata for "update" operation to succeed.
        """
        verbose("Preparing branch config for update")
        access_level_keys_map = {
            "merge_access_level": "allowed_to_merge",
            "push_access_level": "allowed_to_push",
            "unprotect_access_level": "allowed_to_unprotect",
        }
        allowed_to_keys_map = [v for k, v in access_level_keys_map.items()]
        new_branch_config = our_branch_config.copy()
        for key in our_branch_config:
            if key in access_level_keys_map:
                access_level = new_branch_config.pop(key)
                new_branch_config_key = access_level_keys_map[key]
                new_branch_config[new_branch_config_key] = [{"id": None, "access_level": access_level}]

                access_level_key_plural = "{}s".format(key)
                for gl_item in gitlab_branch_config.asdict()[access_level_key_plural]:
                    if gl_item["access_level"] == access_level:
                        new_branch_config[new_branch_config_key][0]["id"] = gl_item["id"]
                    else:
                        new_branch_config[new_branch_config_key].append({"id": gl_item["id"], "_destroy": True})
            elif key in allowed_to_keys_map:
                # this one is tricky...
                # if we got to this point - this means that there is /some/
                # difference between our local config and state in gitlab.
                # we don't know where the difference is - let's figure it out:
                # 1- access_levels existing in both our and gitlab branch config
                #    are no-op (but we need to identify those, as attempt to create
                #    access_level that's already in GitLab will raise an error on
                #    GitLab side)
                # 2- access_levels existing only in our config - need to be created
                # 3- access_levels existing only in gitlab config - should be removed
                # The above is valid for user_id and group_id entries too.

                access_levels_on_both_sides = []
                for idx, our_item in enumerate(our_branch_config[key]):
                    found_items = [
                        (idx, gl_item["id"])
                        for gl_item in gitlab_branch_config.merge_access_levels
                        if gl_item["access_level"] == our_item["access_level"]
                        or gl_item["user_id"] == our_item["user_id"]
                        or gl_item["group_id"] == our_item["group_id"]
                    ]
                    if len(found_items) > 0:
                        access_levels_on_both_sides.append(found_items[0])
                for item in access_levels_on_both_sides:
                    access_level_idx = item[0]
                    access_level_id = item[1]
                    new_branch_config[key][access_level_idx]["id"] = access_level_id
                # remove access_levels from GitLab that are not listed in our
                # config already
                for gl_item in gitlab_branch_config.merge_access_levels:
                    if gl_item["id"] not in [item[1] for item in access_levels_on_both_sides]:
                        self.gitlab._make_request_to_api(
                            "projects/%s/protected_branches/%s",
                            (gitlab_branch_config.id, gitlab_branch_config.name),
                            "PATCH",
                            None,
                            [200],
                            {key: [{"_destroy": "true", "id": gl_item["id"]}]},
                        )
        return new_branch_config

    def transform_branch_config_access_levels(
        self, our_branch_config: dict, gitlab_branch_config: dict, prepare_for_update: bool = False
    ):
        """Branch protection CRUD API in python-gitlab (and GitLab itself) is
        inconsistent, the structure needed to create a branch protection rule is
        different from structure needed to update a rule in place.
        Also, "protected" attribute is missing from GitLab side of things.
        This method will normalize gitlabform branch_config to accomodate this.
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

    def transform_branch_config(self, branch_config: dict):
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
            if item["access_level"] >= 0:
                access_level = item["access_level"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["access_level"] != access_level:
                        changes_found += 1
            elif item["user_id"] >= 0:
                user_id = item["user_id"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["user_id"] != user_id:
                        changes_found += 1
            elif item["group_id"] >= 0:
                group_id = item["group_id"]
                for gl_item in cfg_in_gitlab:
                    if gl_item["group_id"] != group_id:
                        changes_found += 1
        if changes_found > 0: needs_update = True
        debug(f"naive_access_level_diff_analyzer - needs_update: {needs_update}, changes_found: {changes_found}")
        return needs_update

    @staticmethod
    def is_branch_name_wildcard(branch):
        return "*" in branch or "?" in branch
