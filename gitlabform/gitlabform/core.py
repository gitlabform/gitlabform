import argparse
import logging.config
import re
import traceback
import sys
from pathlib import Path
import os
from functools import wraps

from gitlabform.configuration import Configuration
from gitlabform.configuration.core import ConfigFileNotFoundException
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import TestRequestFailedException, UnexpectedResponseException
from gitlabform.gitlab.core import NotFoundException


def if_in_config_and_not_skipped(method):
    """
    This is a universal method of making some config parts skippable because of missing config or explicit "skip: true"
    in it.

    This wrapper function if it is applied on a method with a name like "process_members" looks for "members" in the
    effective config of a project (method name with "process_" omitted).
    If it does not exist - then this method is skipped.
    If it does exist but contains a key "skip: true" - then this method is also skipped.
    """

    @wraps(method)
    def method_wrapper(self, project_and_group, configuration):

        wrapped_method_name = method.__name__
        # for method name like "process_hooks" this returns "hooks"
        config_section_name = '_'.join(wrapped_method_name.split('_')[1:])

        if config_section_name in configuration:
            if 'skip' in configuration[config_section_name] and configuration[config_section_name]['skip']:
                logging.info("Skipping %s - explicitly configured to do so." % config_section_name)
            else:
                logging.info("Setting %s" % config_section_name)
                return method(self, project_and_group, configuration)
        else:
            logging.debug("Skipping %s - not in config." % config_section_name)

    return method_wrapper


class SafeDict(dict):
    """
    A dict that a "get" method that allows to use a path-like reference to its subdict values.

    For example with a dict like {"key": {"subkey": {"subsubkey": "value"}}}
    you can use a string 'key|subkey|subsubkey' to get the 'value'.

    The default value is returned if ANY of the subelements does not exist.

    Code based on https://stackoverflow.com/a/44859638/2693875
    """
    def get(self, path, default=None):
        keys = path.split('|')
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break

        return val


def configuration_to_safe_dict(method):
    """
    This wrapper function calls the method with the configuration converted from a regular dict into a SafeDict
    """
    @wraps(method)
    def method_wrapper(self, project_and_group, configuration):

        return method(self, project_and_group, SafeDict(configuration))

    return method_wrapper


class GitLabFormCore(object):

    def __init__(self, project_or_group=None, config_string=None, debug=False):

        if project_or_group and config_string:
            self.project_or_group = project_or_group
            self.config_string = config_string
            self.verbose = False
            self.debug = bool(debug)
            self.strict = True
            self.start_from = 1
            self.noop = False
            self.set_log_level(tests=True)
        else:
            self.project_or_group, self.config, self.verbose, self.debug, self.strict, self.start_from, self.noop \
                = self.parse_args()
            self.set_log_level()

        self.gl, self.c = self.initialize_configuration_and_gitlab()

    def parse_args(self):

        parser = argparse.ArgumentParser(description='Easy configuration as code tool for GitLab'
                                                     ' using config in plain YAML.',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('project_or_group',
                            help='Project name in "group/project" format'
                                 'OR a single group name '
                                 'OR "ALL_DEFINED" to run for all groups and projects defined the config'
                                 'OR "ALL" to run for all projects that you have access to')

        parser.add_argument('-c', '--config', default='config.yml', help='Config file path and filename')

        group_ex = parser.add_mutually_exclusive_group()

        group_ex.add_argument('-v', '--verbose', action="store_true", help='Verbose mode')

        group_ex.add_argument('-d', '--debug', action="store_true", help='Debug mode (most verbose)')

        parser.add_argument('--strict', '-s', action="store_true", help='Stop on missing branches and tags')

        parser.add_argument('--start-from', dest='start_from', default=1, type=int,
                            help='Start processing projects from the given one '
                                 '(as numbered by "[x/y] Processing: group/project" messages)')

        parser.add_argument('-n', '--noop', dest='noop', action="store_true", help='Run in no-op (dry run) mode')

        args = parser.parse_args()

        return args.project_or_group, args.config, args.verbose, args.debug, args.strict, args.start_from, args.noop

    def set_log_level(self, tests=False):

        logging.basicConfig()
        level = logging.WARNING
        if self.verbose:
            level = logging.INFO
        elif self.debug:
            level = logging.DEBUG
        logging.getLogger().setLevel(level)

        if not tests:
            fmt = logging.Formatter("%(message)s")
            logging.getLogger().handlers[0].setFormatter(fmt)
        else:
            # disable printing to stdout/err because pytest will catch it anyway
            handler = logging.getLogger().handlers[0]
            logging.getLogger().removeHandler(handler)

    def initialize_configuration_and_gitlab(self):

        try:
            if hasattr(self, 'config_string'):
                gl = GitLab(config_string=self.config_string)
                c = Configuration(config_string=self.config_string)
            else:
                gl = GitLab(self.config.strip())
                c = Configuration(self.config.strip())
            return gl, c
        except ConfigFileNotFoundException as e:
            logging.fatal('Aborting - config file not found at: %s', e)
            sys.exit(1)
        except TestRequestFailedException as e:
            logging.fatal("Aborting - GitLab test request failed, details: '%s'", e)
            sys.exit(2)

    def main(self):
        projects_and_groups, groups = self.get_projects_list()
        self.process_all(projects_and_groups, groups)

    def get_projects_list(self):

        groups = []
        projects_and_groups = []

        if self.project_or_group == "ALL":
            # all projects from all groups we have access to
            logging.warning('>>> Processing ALL groups and and projects')
            groups = self.gl.get_groups()
        elif self.project_or_group == "ALL_DEFINED":
            logging.warning('>>> Processing ALL groups and projects defined in config')
            # all groups from config
            groups = self.c.get_groups()
            # and all projects from config
            projects_and_groups = set(self.c.get_projects())
        else:
            if '/' in self.project_or_group:
                try:
                    self.gl._get_group_id(self.project_or_group)
                    # it's a subgroup
                    groups = [self.project_or_group]
                except NotFoundException:
                    # it's a single project
                    projects_and_groups = [self.project_or_group]
            else:
                # it's a single group
                groups = [self.project_or_group]

        # skip groups before getting projects from gitlab to save time
        if groups:
            if self.c.get_skip_groups():
                effective_groups = [x for x in groups if x not in self.c.get_skip_groups()]
            else:
                effective_groups = groups
        else:
            effective_groups = []

        # gitlab can return single project in a few groups, so let's use a set for projects
        projects_and_groups = set(projects_and_groups)
        for group in effective_groups:
            for project in self.gl.get_projects(group):
                projects_and_groups.add(project)
        projects_and_groups = sorted(list(projects_and_groups))

        # skip projects after getting projects from gitlab
        if self.c.get_skip_projects():
            effective_projects_and_groups = [x for x in projects_and_groups if x not in self.c.get_skip_projects()]
        else:
            effective_projects_and_groups = projects_and_groups

        logging.warning('*** # of groups to process: %s', str(len(groups)))
        logging.warning('*** # of projects to process: %s', str(len(effective_projects_and_groups)))

        return effective_projects_and_groups, effective_groups

    def process_all(self, projects_and_groups, groups):

        i = 0

        for group in groups:
            configuration = self.c.get_effective_config_for_group(group)
            self.process_group_secret_variables(group, configuration)
            self.process_group_settings(group, configuration)
            self.process_group_members(group, configuration)

        for project_and_group in projects_and_groups:

            i += 1

            if i < self.start_from:
                logging.warning('$$$ [%s/%s] Skipping: %s...', i, len(projects_and_groups), project_and_group)
                continue

            logging.warning('* [%s/%s] Processing: %s', i, len(projects_and_groups), project_and_group)

            configuration = self.c.get_effective_config_for_project(project_and_group)

            try:

                if self.noop:
                    logging.warning('Not actually processing because running in noop mode.')
                    logging.debug('Configuration that would be applied: %s' % str(configuration))
                    continue

                self.process_project(project_and_group, configuration)
                self.process_project_settings(project_and_group, configuration)
                self.process_project_push_rules(project_and_group, configuration)
                self.process_merge_requests(project_and_group, configuration)
                self.process_deploy_keys(project_and_group, configuration)
                self.process_secret_variables(project_and_group, configuration)
                self.process_branches(project_and_group, configuration)
                self.process_tags(project_and_group, configuration)
                self.process_services(project_and_group, configuration)
                self.process_files(project_and_group, configuration)
                self.process_hooks(project_and_group, configuration)
                self.process_members(project_and_group, configuration)

            except Exception as e:
                logging.error("+++ Error while processing '%s'", project_and_group)
                traceback.print_exc()

            logging.debug('@ [%s/%s] FINISHED Processing: %s', i, len(projects_and_groups), project_and_group)

    @if_in_config_and_not_skipped
    def process_project_settings(self, project_and_group, configuration):
        project_settings = configuration['project_settings']
        logging.debug("Project settings BEFORE: %s", self.gl.get_project_settings(project_and_group))
        logging.info("Setting project settings: %s", project_settings)
        self.gl.put_project_settings(project_and_group, project_settings)
        logging.debug("Project settings AFTER: %s", self.gl.get_project_settings(project_and_group))

    @if_in_config_and_not_skipped
    def process_project_push_rules(self, project_and_group: str, configuration):
        push_rules = configuration['project_push_rules']
        old_project_push_rules = self.gl.get_project_push_rules(project_and_group)
        logging.debug("Project push rules settings BEFORE: %s", old_project_push_rules)
        if old_project_push_rules:
            logging.info("Updating project push rules: %s", push_rules)
            self.gl.put_project_push_rules(project_and_group, push_rules)
        else:
            logging.info("Creating project push rules: %s", push_rules)
            self.gl.post_project_push_rules(project_and_group, push_rules)
        logging.debug("Project push rules AFTER: %s", self.gl.get_project_push_rules(project_and_group))

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_merge_requests(self, project_and_group, configuration):
        approvals = configuration.get('merge_requests|approvals')
        if approvals:
            logging.info("Setting approvals settings: %s", approvals)
            self.gl.post_approvals_settings(project_and_group, approvals)

        approvers = configuration.get('merge_requests|approvers')
        approver_groups = configuration.get('merge_requests|approver_groups')
        # checking if "is not None" allows configs with empty array to work
        if approvers is not None or approver_groups is not None \
                and approvals and 'approvals_before_merge' in approvals:

            # because of https://gitlab.com/gitlab-org/gitlab/issues/198770 we cannot set more than 1 user
            # or 1 group as approvers, sorry
            if (approvers and len(approvers) > 1) or (approver_groups and len(approver_groups) > 1):
                logging.fatal("Because of https://gitlab.com/gitlab-org/gitlab/issues/198770 you cannot set more than "
                              "1 user or 1 group as approvers, sorry."
                              "Please see https://github.com/egnyte/gitlabform/issues/68#issuecomment-581003703 "
                              "for information about a possible workaround for this limitation.")
                sys.exit(4)

            # in pre-12.3 API approvers (users and groups) were configured under the same endpoint as approvals settings
            approvals_settings = self.gl.get_approvals_settings(project_and_group)
            if 'approvers' in approvals_settings or 'approver_groups' in approvals_settings:
                logging.debug("Deleting legacy approvers setup")
                self.gl.delete_legacy_approvers(project_and_group)

            approval_rule_name = 'Approvers (configured using GitLabForm)'

            # is a rule already configured and just needs updating?
            approval_rule_id = None
            rules = self.gl.get_approvals_rules(project_and_group)
            for rule in rules:
                if rule['name'] == approval_rule_name:
                    approval_rule_id = rule['id']
                    break

            if not approvers:
                approvers = []
            if not approver_groups:
                approver_groups = []

            if approval_rule_id:
                # the rule exists, needs an update
                logging.info("Updating approvers rule to users %s and groups %s" % (approvers, approver_groups))
                self.gl.update_approval_rule(project_and_group, approval_rule_id, approval_rule_name,
                                             approvals['approvals_before_merge'], approvers, approver_groups)
            else:
                # the rule does not exist yet, let's create it
                logging.info("Creating approvers rule to users %s and groups %s" % (approvers, approver_groups))
                self.gl.create_approval_rule(project_and_group, approval_rule_name,
                                             approvals['approvals_before_merge'], approvers, approver_groups)

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_members(self, project_and_group, configuration):
        groups = configuration.get('members|groups')
        if groups:
            for group in groups:
                logging.debug("Setting group '%s' as a member", group)
                access = groups[group]['group_access'] if \
                        'group_access' in groups[group] else None
                expiry = groups[group]['expires_at'] if \
                        'expires_at' in groups[group] else ""

                # we will remove group access first and then re-add them,
                # to ensure that the groups have the expected access level
                self.gl.unshare_with_group(project_and_group, group)
                self.gl.share_with_group(project_and_group, group, access, expiry)

        users = configuration.get('members|users')
        if users:
            for user in users:
                logging.debug("Setting user '%s' as a member", user)
                access = users[user]['access_level'] if \
                        'access_level' in users[user] else None
                expiry = users[user]['expires_at'] if \
                        'expires_at' in users[user] else ""
                self.gl.remove_member_from_project(project_and_group, user)
                self.gl.add_member_to_project(project_and_group, user, access, expiry)

    @if_in_config_and_not_skipped
    def process_deploy_keys(self, project_and_group, configuration):
        logging.debug("Deploy keys BEFORE: %s", self.gl.get_deploy_keys(project_and_group))
        for deploy_key in sorted(configuration['deploy_keys']):
            logging.info("Setting deploy key: %s", deploy_key)
            self.gl.post_deploy_key(project_and_group, configuration['deploy_keys'][deploy_key])
        logging.debug("Deploy keys AFTER: %s", self.gl.get_deploy_keys(project_and_group))

    @if_in_config_and_not_skipped
    def process_secret_variables(self, project_and_group, configuration):
        if not self.gl.get_project_settings(project_and_group)['jobs_enabled']:
            logging.warning("Jobs (CI) not enabled in this project so I can't set secret variables here.")
            return

        logging.debug("Secret variables BEFORE: %s", self.gl.get_secret_variables(project_and_group))
        for secret_variable in sorted(configuration['secret_variables']):
            logging.info("Setting secret variable: %s", secret_variable)

            try:
                current_value = \
                    self.gl.get_secret_variable(project_and_group,
                                                configuration['secret_variables'][secret_variable]['key'])
                if current_value != configuration['secret_variables'][secret_variable]['value']:
                    self.gl.put_secret_variable(project_and_group,
                                                configuration['secret_variables'][secret_variable])
            except NotFoundException:
                self.gl.post_secret_variable(project_and_group,
                                             configuration['secret_variables'][secret_variable])

        logging.debug("Secret variables AFTER: %s", self.gl.get_secret_variables(project_and_group))

    @if_in_config_and_not_skipped
    def process_group_secret_variables(self, group, configuration):
        logging.debug("Group secret variables BEFORE: %s", self.gl.get_group_secret_variables(group))
        for secret_variable in sorted(configuration['group_secret_variables']):
            logging.info("Setting group secret variable: %s", secret_variable)

            try:
                current_value = \
                    self.gl.get_group_secret_variable(group,
                                                configuration['group_secret_variables'][secret_variable]['key'])
                if current_value != configuration['group_secret_variables'][secret_variable]['value']:
                    self.gl.put_group_secret_variable(group,
                                                configuration['group_secret_variables'][secret_variable])
            except NotFoundException:
                self.gl.post_group_secret_variable(group,
                                             configuration['group_secret_variables'][secret_variable])

        logging.debug("Groups secret variables AFTER: %s", self.gl.get_group_secret_variables(group))

    @if_in_config_and_not_skipped
    def process_group_settings(self, group, configuration):
        group_settings = configuration['group_settings']
        logging.debug("Group settings BEFORE: %s", self.gl.get_group_settings(group))
        logging.info("Setting group settings: %s", group_settings)
        self.gl.put_group_settings(group, group_settings)
        logging.debug("Group settings AFTER: %s", self.gl.get_group_settings(group))

    @if_in_config_and_not_skipped
    def process_group_members(self, group, configuration):

        users_to_set_by_username = configuration.get('group_members')
        if users_to_set_by_username:

            # group users before by username
            users_before = self.gl.get_group_members(group)
            logging.debug("Group members BEFORE: %s", users_before)
            users_before_by_username = dict()
            for user in users_before:
                users_before_by_username[user['username']] = user

            # group users to set by access level
            users_to_set_by_access_level = dict()
            for user in users_to_set_by_username:
                access_level = users_to_set_by_username[user]['access_level']
                users_to_set_by_access_level.setdefault(access_level, []).append(user)

            # check if the configured users contain at least one Owner
            if 50 not in users_to_set_by_access_level.keys() and configuration.get('enforce_group_members'):
                logging.fatal("With 'enforce_group_members' flag you cannot have no Owners (access_level = 50) in your "
                              " group members config. GitLab requires at least 1 Owner per group.")
                sys.exit(4)

            # we HAVE TO start configuring access from Owners to prevent case when there is no Owner
            # in a group
            for level in [50, 40, 30, 20, 10]:

                users_to_set_with_this_level = users_to_set_by_access_level[level] \
                    if level in users_to_set_by_access_level else []

                for user in users_to_set_with_this_level:

                    access_level_to_set = users_to_set_by_username[user]['access_level']
                    expires_at_to_set = users_to_set_by_username[user]['expires_at'] \
                        if 'expires_at' in users_to_set_by_username[user] else None

                    if user in users_before_by_username:

                        access_level_before = users_before_by_username[user]['access_level']
                        expires_at_before = users_before_by_username[user]['expires_at']

                        if access_level_before == access_level_to_set and expires_at_before == expires_at_to_set:
                            logging.debug("Nothing to change for user '%s' - same config now as to set.")
                        else:
                            logging.debug("Re-adding user '%s' to change their access level or expires at.")
                            # we will remove the user first and then re-add they,
                            # to ensure that the user has the expected access level
                            self.gl.remove_member_from_group(group, user)
                            self.gl.add_member_to_group(group, user, access_level_to_set, expires_at_to_set)

                    else:
                        logging.debug("Adding user '%s' who previously was not a member.")
                        self.gl.add_member_to_group(group, user, access_level_to_set, expires_at_to_set)

            if configuration.get('enforce_group_members'):
                # remove users not configured explicitly
                # note: only direct members are removed - inherited are left
                users_not_configured = set([user['username'] for user in users_before]) - set(users_to_set_by_username.keys())
                for user in users_not_configured:
                    logging.debug("Removing user '%s' who is not configured to be a member.")
                    self.gl.remove_member_from_group(group, user)
            else:
                logging.debug("Not enforcing group members.")

            logging.debug("Group members AFTER: %s", self.gl.get_group_members(group))

        else:

            logging.fatal("You cannot configure a group to have no members. GitLab requires a group "
                          " to contain at least 1 member who is an Owner (access_level = 50).")
            sys.exit(4)

    @if_in_config_and_not_skipped
    def process_branches(self, project_and_group, configuration):
        for branch in sorted(configuration['branches']):
            try:
                if configuration['branches'][branch]['protected']:
                    logging.debug("Setting branch '%s' as *protected*", branch)
                    # unprotect first to reset 'allowed to merge' and 'allowed to push' fields
                    self.gl.unprotect_branch(project_and_group, branch)
                    self.gl.protect_branch(project_and_group, branch,
                                           configuration['branches'][branch]['developers_can_push'],
                                           configuration['branches'][branch]['developers_can_merge'])
                else:
                    logging.debug("Setting branch '%s' as unprotected", branch)
                    self.gl.unprotect_branch(project_and_group, branch)
            except NotFoundException:
                logging.warning("! Branch '%s' not found when trying to set it as protected/unprotected",
                                branch)
                if self.strict:
                    exit(3)

    @if_in_config_and_not_skipped
    def process_tags(self, project_and_group, configuration):
        for tag in sorted(configuration['tags']):
            try:
                if configuration['tags'][tag]['protected']:
                    create_access_level = configuration['tags'][tag]['create_access_level'] if \
                        'create_access_level' in configuration['tags'][tag] else None
                    logging.debug("Setting tag '%s' as *protected*", tag)
                    try:
                        # try to unprotect first
                        self.gl.unprotect_tag(project_and_group, tag)
                    except NotFoundException:
                        pass
                    self.gl.protect_tag(project_and_group, tag, create_access_level)
                else:
                    logging.debug("Setting tag '%s' as *unprotected*", tag)
                    self.gl.unprotect_tag(project_and_group, tag)
            except NotFoundException:
                logging.warning("! Tag '%s' not found when trying to set it as protected/unprotected", tag)
                if self.strict:
                    exit(3)

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_services(self, project_and_group, configuration):
        for service in sorted(configuration['services']):
            if configuration.get('services|' + service + '|delete'):
                logging.debug("Deleting service '%s'", service)
                self.gl.delete_service(project_and_group, service)
            else:
                try:
                    if service == 'jira':
                        # try to workaround https://github.com/egnyte/gitlabform/issues/69 :
                        # JIRA service changes seem to not work, so lets try to recreate it each time
                        self.gl.get_service(project_and_group, 'jira')
                        logging.debug("Deleting the existing JIRA service first as a workaround for GitLab issue")
                        self.gl.delete_service(project_and_group, 'jira')
                except NotFoundException:
                    logging.debug("Service was not configured before.")

                logging.debug("Setting service '%s'", service)
                self.gl.set_service(project_and_group, service, configuration['services'][service])

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_files(self, project_and_group, configuration):
        for file in sorted(configuration['files']):
            logging.debug("Processing file '%s'...", file)

            if configuration.get('files|' + file + '|skip'):
                logging.debug("Skipping file '%s'", file)
                continue

            all_branches = self.gl.get_branches(project_and_group)
            if configuration['files'][file]['branches'] == 'all':
                branches = sorted(all_branches)
            elif configuration['files'][file]['branches'] == 'protected':
                protected_branches = self.gl.get_protected_branches(project_and_group)
                branches = sorted(protected_branches)
            else:
                branches = []
                for branch in configuration['files'][file]['branches']:
                    if branch in all_branches:
                        branches.append(branch)
                    else:
                        logging.warning("! Branch '%s' not found, not processing file '%s' in it", branch,
                                        file)
                        if self.strict:
                            exit(3)

            for branch in branches:
                logging.info("Processing file '%s' in branch '%s'", file, branch)

                # unprotect protected branch temporarily for operations below
                if configuration.get('branches|' + branch + '|protected'):
                    logging.debug("> Temporarily unprotecting the branch for managing files in it...")
                    self.gl.unprotect_branch(project_and_group, branch)

                if configuration.get('files|' + file + '|delete'):
                    try:
                        self.gl.get_file(project_and_group, branch, file)
                        logging.debug("Deleting file '%s' in branch '%s'", file, branch)
                        self.gl.delete_file(project_and_group, branch, file,
                                            self.get_commit_message_for_file_change(
                                                'delete', configuration.get('files|' + file + '|skip_ci'))
                                            )
                    except NotFoundException:
                        logging.debug("Not deleting file '%s' in branch '%s' (already doesn't exist)", file,
                                      branch)
                else:
                    # change or create file

                    if configuration.get('files|' + file + '|content') \
                            and configuration.get('files|' + file + '|file'):
                        logging.fatal("File '%s' in '%s' has both `content` and `file` set - "
                                      "use only one of these keys.", file, project_and_group)
                        exit(4)
                    elif configuration.get('files|' + file + '|content'):
                        new_content = configuration.get('files|' + file + '|content')
                    else:
                        path_in_config = Path(configuration.get('files|' + file + '|file'))
                        if path_in_config.is_absolute():
                            path = path_in_config.read_text()
                        else:
                            # relative paths are relative to config file location
                            path = Path(os.path.join(self.c.config_dir, str(path_in_config)))
                        new_content = path.read_text()

                    if configuration.get('files|' + file + '|template', True):
                        new_content = self.get_file_content_as_template(
                            new_content,
                            project_and_group,
                            **configuration.get('files|' + file + '|jinja_env', dict()))

                    try:
                        current_content = self.gl.get_file(project_and_group, branch, file)
                        if current_content != new_content:
                            if configuration.get('files|' + file + '|overwrite'):
                                logging.debug("Changing file '%s' in branch '%s'", file, branch)
                                self.gl.set_file(project_and_group, branch, file,
                                                 new_content,
                                                 self.get_commit_message_for_file_change(
                                                     'change', configuration.get('files|' + file + '|skip_ci'))
                                                 )
                            else:
                                logging.debug("Not changing file '%s' in branch '%s' "
                                              "(overwrite flag not set)", file, branch)
                        else:
                            logging.debug("Not changing file '%s' in branch '%s' (it\'s content is already"
                                          " as provided)", file, branch)
                    except NotFoundException:
                        logging.debug("Creating file '%s' in branch '%s'", file, branch)
                        self.gl.add_file(project_and_group, branch, file,
                                         new_content,
                                         self.get_commit_message_for_file_change(
                                             'add', configuration.get('files|' + file + '|skip_ci'))
                                         )

                # protect branch back after above operations
                if configuration.get('branches|' + branch + '|protected'):
                    logging.debug("> Protecting the branch again.")
                    self.gl.protect_branch(project_and_group, branch,
                                           configuration['branches'][branch]['developers_can_push'],
                                           configuration['branches'][branch]['developers_can_merge'])

                if configuration.get('files|' + file + '|only_first_branch'):
                    logging.info('Skipping other branches for this file, as configured.')
                    break

    def get_commit_message_for_file_change(self, operation, skip_build):

        # add '[skip ci]' to commit message to skip CI job, as documented at
        # https://docs.gitlab.com/ee/ci/yaml/README.html#skipping-jobs
        skip_build_str = ' [skip ci]' if skip_build else ''

        return "Automated %s made by gitlabform%s" % (operation, skip_build_str)

    def get_file_content_as_template(self, template, project_and_group, **kwargs):
        # Use jinja with variables project and group
        from jinja2 import Template
        return Template(template).render(
            project=self.get_project(project_and_group),
            group=self.get_group(project_and_group),
            **kwargs)

    def get_group(self, project_and_group):
        return re.match('(.*)/.*', project_and_group).group(1)

    def get_project(self, project_and_group):
        return re.match('.*/(.*)', project_and_group).group(1)

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_hooks(self, project_and_group, configuration):
        for hook in sorted(configuration['hooks']):

            if configuration.get('hooks|' + hook + '|delete'):
                hook_id = self.gl.get_hook_id(project_and_group, hook)
                if hook_id:
                    logging.debug("Deleting hook '%s'", hook)
                    self.gl.delete_hook(project_and_group, hook_id)
                else:
                    logging.debug("Not deleting hook '%s', because it doesn't exist", hook)
            else:
                hook_id = self.gl.get_hook_id(project_and_group, hook)
                if hook_id:
                    logging.debug("Changing existing hook '%s'", hook)
                    self.gl.put_hook(project_and_group, hook_id, hook, configuration['hooks'][hook])
                else:
                    logging.debug("Creating hook '%s'", hook)
                    self.gl.post_hook(project_and_group, hook, configuration['hooks'][hook])

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_project(self, project_and_group, configuration):
        project = configuration['project']
        if project:
            if 'archive' in project:
                if project['archive']:
                    logging.info("Archiving project...")
                    self.gl.archive(project_and_group)
                else:
                    logging.info("Unarchiving project...")
                    self.gl.unarchive(project_and_group)
