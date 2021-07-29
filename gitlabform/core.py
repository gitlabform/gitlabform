import argparse
import logging.config
import platform
import sys
import textwrap
import traceback

import cli_ui


from gitlabform import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.configuration.core import ConfigFileNotFoundException
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import TestRequestFailedException
from gitlabform.input import GroupsAndProjectsProvider
from gitlabform.output import EffectiveConfiguration
from gitlabform.processors.group import GroupProcessors
from gitlabform.processors.project import ProjectProcessors
from gitlabform.ui import (
    info_group_count,
    info_project_count,
    show_version,
    show_summary,
)


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


class GitLabForm(object):
    def __init__(self, project_or_group=None, config_string=None):

        if project_or_group and config_string:
            # this mode is basically only for testing

            self.project_or_group = project_or_group
            self.config_string = config_string
            self.verbose = True
            self.debug = True
            self.strict = True
            self.start_from = 1
            self.start_from_group = 1
            self.noop = False
            self.output_file = None
            self.skip_version_check = True
            self.include_archived_projects = True  # for unarchive tests
            self.just_show_version = False
            self.terminate_after_error = True

            self.configure_output(tests=True)
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
                self.output_file,
                self.skip_version_check,
                self.include_archived_projects,
                self.just_show_version,
                self.terminate_after_error,
            ) = self.parse_args()

            self.configure_output()

            show_version(self.skip_version_check)
            if self.just_show_version:
                sys.exit(0)

            if not self.project_or_group:
                cli_ui.error("project_or_group parameter is required.")
                sys.exit(EXIT_INVALID_INPUT)

        self.gitlab, self.configuration = self.initialize_configuration_and_gitlab()

        self.group_processors = GroupProcessors(self.gitlab)
        self.project_processors = ProjectProcessors(
            self.gitlab, self.configuration, self.strict
        )
        self.groups_and_projects_provider = GroupsAndProjectsProvider(
            self.gitlab, self.configuration, self.include_archived_projects
        )

    def parse_args(self):

        parser = argparse.ArgumentParser(
            description=textwrap.dedent(
                f"""
            Specialized "configuration as a code" tool for GitLab projects, groups and more
            using hierarchical configuration written in YAML.

            Exits with code {EXIT_INVALID_INPUT} on invalid input errors (f.e. config file not found),
            and with code {EXIT_PROCESSING_ERROR} if the are processing errors (f.e. if GitLab returns 400).
            """
            ),
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
            dest="just_show_version",
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
            "-o",
            "--output-file",
            dest="output_file",
            default=None,
            help="name/path of a file to write the effective configs to",
        )

        parser.add_argument(
            "-k",
            "--skip-version-check",
            dest="skip_version_check",
            action="store_true",
            help="Skips checking if the latest version is used",
        )

        parser.add_argument(
            "-a",
            "--include-archived-projects",
            dest="include_archived_projects",
            action="store_true",
            help="Includes processing projects that are archived",
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
            args.output_file,
            args.skip_version_check,
            args.include_archived_projects,
            args.just_show_version,
            args.terminate_after_error,
        )

    def configure_output(self, tests=False):

        # normal mode - print cli_ui.info+ + logging.fatal
        # verbose mode - print cli_ui.* + logging.fatal
        # debug / tests mode - like above + logging.debug

        logging.basicConfig()

        if not self.verbose and not self.debug:  # normal
            cli_ui.setup()
            level = logging.FATAL
        else:
            if (
                self.debug or tests
            ):  # debug (BUT verbose may also be set, that's why we check this first)
                cli_ui.setup(verbose=True)
                level = logging.DEBUG
            elif self.verbose:  # verbose
                cli_ui.setup(verbose=True)
                level = logging.FATAL

        logging.getLogger().setLevel(level)
        fmt = logging.Formatter("%(message)s")
        logging.getLogger().handlers[0].setFormatter(fmt)

    def initialize_configuration_and_gitlab(self):

        try:
            if hasattr(self, "config_string"):
                gitlab = GitLab(config_string=self.config_string)
            else:
                gitlab = GitLab(config_path=self.config)
            configuration = gitlab.get_configuration()
            return gitlab, configuration
        except ConfigFileNotFoundException as e:
            cli_ui.error(f"Config file not found at: {e}")
            sys.exit(EXIT_INVALID_INPUT)
        except TestRequestFailedException as e:
            cli_ui.error(f"GitLab test request failed. Exception: '{e}'")
            sys.exit(EXIT_PROCESSING_ERROR)

    def main(self):
        if self.project_or_group == "ALL":
            cli_ui.info(">>> Processing ALL groups and projects")
        elif self.project_or_group == "ALL_DEFINED":
            cli_ui.info(">>> Processing ALL groups and projects defined in config")

        groups, projects = self.groups_and_projects_provider.get_groups_and_projects(
            self.project_or_group
        )

        if len(groups) == 0 and len(projects) == 0:
            cli_ui.error(f"Entity {self.project_or_group} cannot be found in GitLab!")
            sys.exit(EXIT_INVALID_INPUT)
        else:
            cli_ui.debug(f"groups: {groups}")
            cli_ui.debug(f"projects: {projects}")

        cli_ui.info_1(f"# of groups to process: {len(groups)}")
        cli_ui.info_1(f"# of projects to process: {len(projects)}")

        self.process_all(projects, groups)

    def process_all(self, projects_and_groups, groups):

        group_number = 0
        successful_groups = 0
        failed_groups = {}

        effective_configuration = EffectiveConfiguration(self.output_file)

        for group in groups:

            group_number += 1

            if group_number < self.start_from_group:
                info_group_count(
                    "@",
                    group_number,
                    len(groups),
                    cli_ui.yellow,
                    f"Skipping group {group} as requested to start from {self.start_from_group}...",
                    cli_ui.reset,
                )
                continue

            configuration = self.configuration.get_effective_config_for_group(group)

            effective_configuration.add_placeholder(group)

            if configuration:
                info_group_count(
                    "@", group_number, len(groups), f"Processing group: {group}"
                )

                try:
                    self.group_processors.process_group(
                        group,
                        configuration,
                        dry_run=self.noop,
                        effective_configuration=effective_configuration,
                    )

                    successful_groups += 1

                except Exception as e:

                    failed_groups[group_number] = group

                    trace = traceback.format_exc()
                    message = f"Error occurred while processing group {group}, exception:\n\n{e}\n\n{trace}"

                    if self.terminate_after_error:
                        effective_configuration.write_to_file()
                        cli_ui.error(message)
                        sys.exit(EXIT_PROCESSING_ERROR)
                    else:
                        cli_ui.warning(message)
                finally:
                    logging.debug(
                        f"@ ({group_number}/{len(groups)}) FINISHED Processing group: {group}"
                    )

            else:
                info_group_count(
                    "@",
                    group_number,
                    len(groups),
                    cli_ui.yellow,
                    f"Skipping group {group} as it has empty effective config.",
                    cli_ui.reset,
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
                    f"Skipping project {project_and_group} as requested to start from {self.start_from}...",
                    cli_ui.reset,
                )
                continue

            configuration = self.configuration.get_effective_config_for_project(
                project_and_group
            )

            effective_configuration.add_placeholder(project_and_group)

            if configuration:
                info_project_count(
                    "*",
                    project_number,
                    len(projects_and_groups),
                    f"Processing project: {project_and_group}",
                )

                try:
                    self.project_processors.process_project(
                        project_and_group,
                        configuration,
                        dry_run=self.noop,
                        effective_configuration=effective_configuration,
                    )

                    successful_projects += 1

                except Exception as e:

                    failed_projects[project_number] = project_and_group

                    trace = traceback.format_exc()
                    message = f"Error occurred while processing project {project_and_group}, exception:\n\n{e}\n\n{trace}"

                    if self.terminate_after_error:
                        effective_configuration.write_to_file()
                        cli_ui.error(message)
                        sys.exit(EXIT_PROCESSING_ERROR)
                    else:
                        cli_ui.warning(message)

                finally:

                    logging.debug(
                        f"* ({project_number}/{len(projects_and_groups)}) FINISHED Processing project: {project_and_group}",
                    )
            else:
                info_project_count(
                    "*",
                    project_number,
                    len(projects_and_groups),
                    cli_ui.yellow,
                    f"Skipping project {project_and_group} as it has empty effective config.",
                    cli_ui.reset,
                )

        effective_configuration.write_to_file()

        show_summary(
            successful_groups, successful_projects, failed_groups, failed_projects
        )
