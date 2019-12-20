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
from gitlabform.gitlab.core import TestRequestFailedException
from gitlabform.gitlab.core import NotFoundException


def if_in_config_and_not_skipped(method):

    @wraps(method)
    def method_wrapper(self, project_and_group, configuration):

        wrapped_method_name = method.__name__
        # for method name like "process_hooks" this returns "hooks"
        config_section_name = '_'.join(wrapped_method_name.split('_')[1:])

        if config_section_name in configuration:
            if 'skip' in configuration[config_section_name] and configuration[config_section_name]['skip']:
                logging.debug("Skipping %s - explicitly configured to do so." % config_section_name)
            else:
                logging.debug("Setting %s" % config_section_name)
                return method(self, project_and_group, configuration)
        else:
            logging.debug("Skipping %s - not in config." % config_section_name)

    return method_wrapper

# dict that returns `default` if queried with ".get('key|subkey|subsubkey')" if any of the subkeys doesn't exist
# based on https://stackoverflow.com/a/44859638/2693875
class SafeDict(dict):

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

    @wraps(method)
    def method_wrapper(self, project_and_group, configuration):

        return method(self, project_and_group, SafeDict(configuration))

    return method_wrapper


class GitLabFormCore(object):

    def __init__(self):
        self.args = self.parse_args()
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

        return parser.parse_args()

    def set_log_level(self):

        logging.basicConfig()
        level = logging.WARNING
        if self.args.verbose:
            level = logging.INFO
        elif self.args.debug:
            level = logging.DEBUG
        logging.getLogger().setLevel(level)

        fmt = logging.Formatter("%(message)s")
        logging.getLogger().handlers[0].setFormatter(fmt)

    def initialize_configuration_and_gitlab(self):

        try:
            gl = GitLab(self.args.config.strip(), self.args.noop)
            c = Configuration(self.args.config.strip())
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

        if self.args.project_or_group == "ALL":
            # all projects from all groups we have access to
            logging.warning('>>> Processing ALL groups and and projects')
            groups = self.gl.get_groups()
        elif self.args.project_or_group == "ALL_DEFINED":
            logging.warning('>>> Processing ALL groups and projects defined in config')
            # all groups from config
            groups = self.c.get_groups()
            # and all projects from config
            projects_and_groups = set(self.c.get_projects())
        else:
            if '/' in self.args.project_or_group:
                try:
                    self.gl._get_group_id(self.args.project_or_group)
                    # it's a subgroup
                    groups = [self.args.project_or_group]
                except NotFoundException:
                    # it's a single project
                    projects_and_groups = [self.args.project_or_group]
            else:
                # it's a single group
                groups = [self.args.project_or_group]

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

            if i < self.args.start_from:
                logging.warning('$$$ [%s/%s] Skipping: %s...', i, len(projects_and_groups), project_and_group)
                continue

            logging.warning('/--* [%s/%s] Processing: %s', i, len(projects_and_groups), project_and_group)

            configuration = self.c.get_effective_config_for_project(project_and_group)

            try:
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
                logging.warning('\--* [%s/%s] Done: %s', i, len(projects_and_groups), project_and_group)

            except Exception as e:
                logging.error("+++ Error while processing '%s'", project_and_group)
                traceback.print_exc()

    @if_in_config_and_not_skipped
    def process_project_settings(self, project_and_group, configuration):
        project_settings = configuration['project_settings']
        logging.debug("Project settings BEFORE: %s", self.gl.get_project_settings(project_and_group))
        logging.info("Setting project settings: %s", project_settings)
        self.gl.put_project_settings(project_and_group, project_settings)
        logging.debug("Project settings AFTER: %s", self.gl.get_project_settings(project_and_group))

    @if_in_config_and_not_skipped
    def process_project_push_rules(self, project_and_group, configuration):
        push_rules = configuration['project_push_rules']
        logging.debug("Project push rules settings BEFORE: %s", self.gl.get_project_push_rules(project_and_group))
        logging.info("Setting project push rules: %s", push_rules)
        self.gl.put_project_push_rules(project_and_group, push_rules)
        logging.debug("Project push rules AFTER: %s", self.gl.get_project_push_rules(project_and_group))

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_merge_requests(self, project_and_group, configuration):
        approvals = configuration.get('merge_requests|approvals')
        if approvals:
            logging.info("Setting approvals settings: %s", approvals)
            self.gl.post_approvals(project_and_group, approvals)

        approvers = configuration.get('merge_requests|approvers')
        approver_groups = configuration.get('merge_requests|approver_groups')
        # checking if is not None allows configs with empty array to work
        if approvers is not None or approver_groups is not None:
            if not approvers:
                approvers = []
            if not approver_groups:
                approver_groups = []
            logging.info("Setting approvers to users %s and groups %s" % (approvers, approver_groups))
            self.gl.put_approvers(project_and_group, approvers, approver_groups)

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_members(self, project_and_group, configuration):
        remote_group_shares = self.gl.get_project_group_shares(project_and_group)
        groups = configuration.get('members|groups')
        if groups:
            for group in groups:
                logging.debug("Setting group '%s' as a member", group)
                access = groups[group]['group_access'] if \
                        'group_access' in groups[group] else None
                expiry = groups[group]['expires_at'] if \
                        'expires_at' in groups[group] else ""
                if group not in remote_group_shares.keys(): # TODO: there is actual change to the remote group one in level or expiry
                    # new group share
                    self.gl.share_with_group(project_and_group, group, access, expiry)
                else:
                    remote_expiry = "" if remote_group_shares[group]["expires_at"] == None else remote_group_shares[group]["expires_at"]
                    if remote_group_shares[group]["group_access_level"] != access or remote_expiry != expiry:
                        # data changed of old group share
                        self.gl.update_group_share_of_project(project_and_group,group,access, expiry)

        remote_members = self.gl.get_project_members(project_and_group)
        users = configuration.get('members|users')
        if users:
            for user in users:
                logging.debug("Setting user '%s' as a member", user)
                access = users[user]['access_level'] if \
                        'access_level' in users[user] else None
                expiry = users[user]['expires_at'] if \
                        'expires_at' in users[user] else ""
                if user not in remote_members.keys():
                    # new user
                    self.gl.add_member_to_project(project_and_group, user, access, expiry)
                else:
                    remote_expiry = "" if remote_members[user]["expires_at"] == None else remote_members[user]["expires_at"]
                    if remote_members[user]["access_level"] != access or remote_expiry != expiry:
                        self.gl.update_member_of_project(project_and_group,user, access, expiry)

        if configuration.get('enforce_group_members'):
            # remove groups that are not part of the configuration
            self.enforce_group_shares(project_and_group, groups if groups else [])

        if configuration.get('enforce_user_members'):
            # remove users that are not part of the configuration
            self.enforce_user_shares(project_and_group, users if users else [])

    def enforce_group_shares(self, project_and_group, groups):
        for remote_group_share in self.gl.get_project_group_shares(project_and_group).keys():
            if remote_group_share not in groups:
                self.gl.unshare_with_group(project_and_group, remote_group_share)

    def enforce_user_shares(self, project_and_group, users):
        for user in self.gl.get_project_members(project_and_group).keys():
            if user not in users:
                self.gl.remove_member_from_project(project_and_group, user)

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

    def process_group_members(self, group, configuration):
        members = configuration.get('members')
        users = members.get('users')
        remote_users = self.gl.get_group_members(group)
        if configuration.get('enforce_user_members'):
            for user in remote_users:
                if not users or user not in users:
                    self.gl.remove_member_from_group(group, user)
        if users:
            for username, user in users.items():
                expiry = user['expires_at'] if \
                            'expires_at' in username else ""
                if username in remote_users:
                    self.gl.update_member_of_group(group, username, user['access_level'], expiry)
                else:
                    self.gl.add_member_to_group(group, username, user['access_level'], expiry)


    @if_in_config_and_not_skipped
    def process_group_settings(self, group, configuration):
        group_settings = configuration['group_settings']
        logging.debug("Group settings BEFORE: %s", self.gl.get_group_settings(group))
        logging.info("Setting group settings: %s", group_settings)
        self.gl.put_group_settings(group, group_settings)
        logging.debug("Group settings AFTER: %s", self.gl.get_group_settings(group))

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
                if self.args.strict:
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
                if self.args.strict:
                    exit(3)

    @if_in_config_and_not_skipped
    @configuration_to_safe_dict
    def process_services(self, project_and_group, configuration):
        for service in sorted(configuration['services']):
            if configuration.get('services|' + service + '|delete'):
                logging.debug("Deleting service '%s'", service)
                self.gl.delete_service(project_and_group, service)
            else:
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
            else:
                branches = []
                for branch in configuration['files'][file]['branches']:
                    if branch in all_branches:
                        branches.append(branch)
                    else:
                        logging.warning("! Branch '%s' not found, not processing file '%s' in it", branch,
                                        file)
                        if self.args.strict:
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
