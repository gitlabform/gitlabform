import argparse
import logging.config
import sys
import traceback

import cli_ui
import luddite
import pkg_resources
from packaging import version as packaging_version

from gitlabform import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.configuration import Configuration
from gitlabform.configuration.core import ConfigFileNotFoundException
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform.gitlab.core import TestRequestFailedException
from gitlabform.gitlabform.processors.group import GroupProcessors
from gitlabform.gitlabform.processors.project import ProjectProcessors
from gitlabform.gitlabform.ui import info_group_count, info_project_count


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


class GitLabFormCore(object):
    def __init__(self, project_or_group=None, config_string=None):

        if project_or_group and config_string:
            # this mode is basically only for testing

            self.project_or_group = project_or_group
            self.config_string = config_string
            self.verbose = False
            self.debug = True
            self.strict = True
            self.start_from = 1
            self.start_from_group = 1
            self.noop = False
            self.configure_output(tests=True)
            self.skip_version_check = True
            self.show_version = False
            self.terminate_after_error = True
        else:
            # normal mode

            (
                self.project_or_group,
                self.config,
                self.verbose,
                self.debug,
                self.strict,
                self.start_from,
                self.start_from_group,
                self.noop,
                self.skip_version_check,
                self.show_version,
                self.terminate_after_error,
            ) = self.parse_args()

            self.configure_output()

            cli_ui.info(self.get_version(self.skip_version_check))
            if self.show_version:
                sys.exit(0)

            if not self.project_or_group:
                cli_ui.error("project_or_group parameter is required.")
                sys.exit(EXIT_INVALID_INPUT)

        self.gl, self.c = self.initialize_configuration_and_gitlab()

        self.group_processors = GroupProcessors(self.gl)
        self.project_processors = ProjectProcessors(self.gl, self.c, self.strict)

    def parse_args(self):

        parser = argparse.ArgumentParser(
            description=f"""
Specialized "configuration as a code" tool for GitLab projects, groups and more
using hierarchical configuration written in YAML.

Exits with code {EXIT_INVALID_INPUT} on invalid input errors (f.e. config file not found),
and with code {EXIT_PROCESSING_ERROR} if the are processing errors (f.e. if GitLab returns 400).
            """,
            formatter_class=Formatter,
        )

        parser.add_argument(
            "project_or_group",
            nargs="?",
            help='Project name in "group/project" format '
            "OR a single group name "
            'OR "ALL_DEFINED" to run for all groups and projects defined the config '
            'OR "ALL" to run for all projects that you have access to',
        )

        parser.add_argument(
            "-V",
            "--version",
            dest="show_version",
            action="store_true",
            help="show version and exit",
        )

        parser.add_argument(
            "-c", "--config", default="config.yml", help="config file path and filename"
        )

        verbosity_args = parser.add_mutually_exclusive_group()

        verbosity_args.add_argument(
            "-v", "--verbose", action="store_true", help="verbose mode"
        )

        verbosity_args.add_argument(
            "-d", "--debug", action="store_true", help="debug mode (most verbose)"
        )

        parser.add_argument(
            "-s",
            "--strict",
            action="store_true",
            help="stop on missing branches and tags",
        )

        parser.add_argument(
            "-n",
            "--noop",
            dest="noop",
            action="store_true",
            help="run in no-op (dry run) mode",
        )

        parser.add_argument(
            "-k",
            "--skip-version-check",
            dest="skip_version_check",
            action="store_true",
            help="Skips checking if the latest version is used",
        )

        parser.add_argument(
            "-t",
            "--terminate",
            dest="terminate_after_error",
            action="store_true",
            help=f"exit with {EXIT_PROCESSING_ERROR} after the first group/project processing error."
            f" (default: process all the requested groups/projects and skip the failing ones."
            f" At the end, if there were any groups/projects, exit with {EXIT_PROCESSING_ERROR}.)",
        )

        parser.add_argument(
            "-sf",
            "--start-from",
            dest="start_from",
            default=1,
            type=int,
            help="start processing projects from the given one"
            ' (as numbered by "x/y Processing group/project" messages)',
        )

        parser.add_argument(
            "-sfg",
            "--start-from-group",
            dest="start_from_group",
            default=1,
            type=int,
            help="start processing groups from the given one "
            '(as numbered by "x/y Processing group/project" messages)',
        )

        args = parser.parse_args()

        return (
            args.project_or_group,
            args.config,
            args.verbose,
            args.debug,
            args.strict,
            args.start_from,
            args.start_from_group,
            args.noop,
            args.skip_version_check,
            args.show_version,
            args.terminate_after_error,
        )

    def configure_output(self, tests=False):

        # normal verbosity - print cli_ui.[info, warning, ...]

        # verbose mode - like above plus cli_ui.debug

        # debug mode - like above plus logging.debug

        logging.basicConfig()

        if not self.verbose and not self.debug:
            cli_ui.setup()
            level = logging.FATAL  # de facto disable
        elif self.verbose:
            cli_ui.setup(verbose=True)
            level = logging.FATAL  # de facto disable
        else:
            cli_ui.setup(verbose=True)
            level = logging.DEBUG

        logging.getLogger().setLevel(level)

        if not tests:
            fmt = logging.Formatter("%(message)s")
            logging.getLogger().handlers[0].setFormatter(fmt)
        else:
            # disable printing to stdout/err because pytest will catch it anyway
            handler = logging.getLogger().handlers[0]
            logging.getLogger().removeHandler(handler)

    def get_version(self, skip_version_check):
        local_version = pkg_resources.get_distribution("gitlabform").version
        version = f"GitLabForm version: {local_version}"

        if not skip_version_check:
            latest_version = luddite.get_version_pypi("gitlabform")
            if local_version == latest_version:
                version += " = the latest stable"
            elif packaging_version.parse(local_version) < packaging_version.parse(
                latest_version
            ):
                version += f" = outdated, please update! (the latest stable is {latest_version})"
            else:
                version += f" = pre-release (the latest stable is {latest_version})"

        return version

    def initialize_configuration_and_gitlab(self):

        try:
            if hasattr(self, "config_string"):
                c = Configuration(config_string=self.config_string)
                gl = GitLab(configuration=c)
            else:
                c = Configuration(self.config.strip())
                gl = GitLab(configuration=c)
            return gl, c
        except ConfigFileNotFoundException as e:
            cli_ui.error(f"Config file not found at: {e}")
            sys.exit(EXIT_INVALID_INPUT)
        except TestRequestFailedException as e:
            cli_ui.error(f"GitLab test request failed. Exception: '{e}'")
            sys.exit(EXIT_PROCESSING_ERROR)

    def main(self):
        projects_and_groups, groups = self.get_projects_list()
        self.process_all(projects_and_groups, groups)

    def get_projects_list(self):

        groups = []
        projects_and_groups = []

        if self.project_or_group == "ALL":
            # all projects from all groups we have access to
            cli_ui.info(">>> Processing ALL groups and and projects")
            groups = self.gl.get_groups()
        elif self.project_or_group == "ALL_DEFINED":
            cli_ui.info(">>> Processing ALL groups and projects defined in config")
            # all groups from config
            groups = self.c.get_groups()
            # and all projects from config
            projects_and_groups = set(self.c.get_projects())
        else:
            if "/" in self.project_or_group:
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
                effective_groups = [
                    x for x in groups if x not in self.c.get_skip_groups()
                ]
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
            effective_projects_and_groups = [
                x for x in projects_and_groups if x not in self.c.get_skip_projects()
            ]
        else:
            effective_projects_and_groups = projects_and_groups

        cli_ui.info_1(f"# of groups to process: {len(groups)}")
        cli_ui.info_1(f"# of projects to process: {len(effective_projects_and_groups)}")

        return effective_projects_and_groups, effective_groups

    def process_all(self, projects_and_groups, groups):

        group_number = 0
        successful_groups = 0
        failed_groups = {}

        for group in groups:

            group_number += 1

            if group_number < self.start_from_group:
                info_group_count(
                    "@",
                    group_number,
                    len(groups),
                    cli_ui.yellow,
                    f"Skipping group: {group}...",
                    cli_ui.reset,
                )
                continue

            info_group_count(
                "@", group_number, len(groups), f"Processing group: {group}"
            )

            configuration = self.c.get_effective_config_for_group(group)

            try:
                self.group_processors.process_group(
                    group, configuration, dry_run=self.noop
                )

                successful_groups += 1

            except Exception as e:

                failed_groups[group_number] = group

                trace = traceback.format_exc()
                message = f"Error occurred while processing group {group}, exception:\n\n{e}\n\n{trace}"

                if self.terminate_after_error:
                    cli_ui.error(message)
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    cli_ui.warning(message)

            logging.debug(
                f"@ ({group_number}/{len(groups)}) FINISHED Processing group: {group}"
            )

        project_number = 0
        successful_projects = 0
        failed_projects = {}

        for project_and_group in projects_and_groups:

            project_number += 1

            if project_number < self.start_from:
                info_project_count(
                    "*",
                    project_number,
                    len(projects_and_groups),
                    cli_ui.yellow,
                    f"Skipping project: {project_and_group}...",
                    cli_ui.reset,
                )
                continue

            info_project_count(
                "*",
                project_number,
                len(projects_and_groups),
                f"Processing project: {project_and_group}",
            )

            configuration = self.c.get_effective_config_for_project(project_and_group)

            try:
                self.project_processors.process_project(
                    project_and_group, configuration, dry_run=self.noop
                )

                successful_projects += 1

            except Exception as e:

                failed_projects[project_number] = project_and_group

                trace = traceback.format_exc()
                message = f"Error occurred while processing project {project_and_group}, exception:\n\n{e}\n\n{trace}"

                if self.terminate_after_error:
                    cli_ui.error(message)
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    cli_ui.warning(message)

            logging.debug(
                f"* ({project_number}/{len(projects_and_groups)}) FINISHED Processing project: {project_and_group}",
            )

        cli_ui.info_1(f"# of groups processed successfully: {successful_groups}")
        cli_ui.info_1(f"# of projects processed succesfully: {successful_projects}")

        if len(failed_groups) > 0:
            cli_ui.info_1(
                cli_ui.red, f"# of groups failed: {len(failed_groups)}", cli_ui.reset
            )
            for group_number in failed_groups.keys():
                cli_ui.info_1(
                    cli_ui.red,
                    f"Failed group {group_number}: {failed_groups[group_number]}",
                    cli_ui.reset,
                )
        if len(failed_projects) > 0:
            cli_ui.info_1(
                cli_ui.red,
                f"# of projects failed: {len(failed_projects)}",
                cli_ui.reset,
            )
            for project_number in failed_projects.keys():
                cli_ui.info_1(
                    cli_ui.red,
                    f"Failed project {project_number}: {failed_projects[project_number]}",
                    cli_ui.reset,
                )

        if len(failed_groups) > 0 or len(failed_projects) > 0:
            sys.exit(EXIT_PROCESSING_ERROR)
        else:
            party = cli_ui.Symbol("🎉", "!!!")
            cli_ui.info_1(
                cli_ui.green,
                f"All requested groups/projects processes successfully!",
                cli_ui.reset,
                party,
            )
