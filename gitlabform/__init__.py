import sys
from logging import debug

import argparse
import cli_ui
import logging
import luddite
import pkg_resources
import textwrap
import traceback
from cli_ui import (
    Symbol,
    reset,
    blue,
    message,
    error,
    info,
    fatal,
    info_1,
    debug as verbose,
    red,
    green,
    yellow,
    Token,
    purple,
    warning,
)
from packaging import version as packaging_version
from typing import Any, Tuple

from gitlabform.configuration import Configuration
from gitlabform.configuration.core import (
    ConfigFileNotFoundException,
    ConfigInvalidException,
)
from gitlabform.configuration.transform import ConfigurationTransformers
from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import TestRequestFailedException
from gitlabform.lists import Entities
from gitlabform.lists.filter import GroupsAndProjectsFilters
from gitlabform.lists.groups import GroupsProvider
from gitlabform.lists.projects import ProjectsProvider
from gitlabform.output import EffectiveConfigurationFile
from gitlabform.processors.group import GroupProcessors
from gitlabform.processors.project import ProjectProcessors


class GitLabForm:
    def __init__(self, include_archived_projects=True, target=None, config_string=None):
        if target and config_string:
            # this mode is basically only for testing

            self.target = target
            self.config_string = config_string
            self.verbose = True
            self.debug = True
            self.strict = True
            self.start_from = 1
            self.start_from_group = 1
            self.noop = False
            self.output_file = None
            self.skip_version_check = True
            self.include_archived_projects = include_archived_projects
            self.just_show_version = False
            self.terminate_after_error = True
            self.only_sections = "all"

            self._configure_output(tests=True)
        else:
            # normal mode

            (
                self.target,
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
                self.only_sections,
            ) = self._parse_args()

            self._configure_output()

            self._show_version(self.skip_version_check)
            if self.just_show_version:
                sys.exit(0)

            if not self.target:
                fatal(
                    "target parameter is required.",
                    exit_code=EXIT_INVALID_INPUT,
                )

        self.gitlab, self.configuration = self._initialize_configuration_and_gitlab()

        self.group_processors = GroupProcessors(
            self.gitlab, self.configuration, self.strict
        )
        self.project_processors = ProjectProcessors(
            self.gitlab, self.configuration, self.strict
        )
        self.groups_provider = GroupsProvider(
            self.gitlab,
            self.configuration,
        )
        self.projects_provider = ProjectsProvider(
            self.gitlab,
            self.configuration,
            self.include_archived_projects,
        )

        self.groups_and_projects_filters = GroupsAndProjectsFilters(
            self.configuration, self.group_processors, self.project_processors
        )

    @staticmethod
    def _parse_args() -> Tuple:
        """
        Parses the input command-line arguments.

        :return: a tuple with all the arguments that have been parsed
        """
        parser = argparse.ArgumentParser(
            description=textwrap.dedent(
                f"""
            🏗 Specialized configuration as a code tool for GitLab projects, groups and more
            using hierarchical configuration written in YAML.

            Exits with code:
              * 0 - on success,
              * {EXIT_INVALID_INPUT} - on invalid input errors (f.e. bad syntax in the config file) ~ "it's your fault". 😅
              * {EXIT_PROCESSING_ERROR} - if there were backend processing errors (f.e. when requests to GitLab fail) ~ "it's not your fault". 😎
            """
            ),
            formatter_class=Formatter,
        )

        parser.add_argument(
            "target",
            nargs="?",
            help='Project name in "group/project" format \n'
            "OR a single group name \n"
            'OR "ALL_DEFINED" to run for all groups and projects defined the config \n'
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
            "-k",
            "--skip-version-check",
            dest="skip_version_check",
            action="store_true",
            help="Skips checking if the latest version is used",
        )

        parser.add_argument(
            "-c", "--config", default="config.yml", help="config file path and filename"
        )

        verbosity_args = parser.add_mutually_exclusive_group()

        verbosity_args.add_argument(
            "-v", "--verbose", action="store_true", help="verbose output"
        )

        verbosity_args.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="debug output (!!! WARNING !!!: sensitive data and secrets may"
            " be printed in this mode - all the data sent to GitLab API"
            " will be printed in plain-text.)",
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
            help="name/path of a file to write the effective configs to"
            " (!!! WARNING !!!: if your config contains sensitive data or secrets, then this file will also"
            " contain them.)",
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

        parser.add_argument(
            "-os",
            "--only-sections",
            dest="only_sections",
            default="all",
            type=str,
            help="process only section with these names (comma-delimited)",
        )

        args = parser.parse_args()

        if args.only_sections != "all":
            args.only_sections = args.only_sections.split(",")

        return (
            args.target,
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
            args.only_sections,
        )

    def _configure_output(self, tests=False) -> None:
        """
        Configures the application output using cli_ui and logging, based on debug and verbose flags:

        * normal mode - print cli_ui.* except debug as verbose
        * verbose mode - print all cli_ui.*, including debug as verbose
        * debug / tests mode - like above + (logging.)debug

        :param tests: True if we are running in tests mode
        """

        logging.basicConfig()

        if self.debug or tests:
            # debug / tests
            cli_ui_verbose = True
            level = logging.DEBUG
        elif self.verbose:
            # verbose
            cli_ui_verbose = True
            # de facto disabled as we don't use logging different from debug in this project
            level = logging.FATAL
        else:
            # normal
            cli_ui_verbose = False
            # de facto disabled as we don't use logging different from debug in this project
            level = logging.FATAL

        cli_ui.setup(verbose=cli_ui_verbose)
        logging.getLogger().setLevel(level)

        fmt = logging.Formatter("%(message)s")
        logging.getLogger().handlers[0].setFormatter(fmt)

    def _initialize_configuration_and_gitlab(self) -> Tuple[GitLab, Configuration]:
        """
        Creates the GitLab object, which represents connection to the GitLab API,
        and the configuration object, which represents the YAML configuration,
        and runs processing the configuration with configuration transformers.

        :return: tuple with GitLab and Configuration objects
        """

        try:
            if hasattr(self, "config_string"):
                gitlab = GitLab(config_string=self.config_string)
            else:
                gitlab = GitLab(config_path=self.config)
            configuration = gitlab.get_configuration()

            configuration_transformers = ConfigurationTransformers(gitlab)
            configuration_transformers.transform(configuration)

        except ConfigFileNotFoundException as e:
            fatal(
                f"Config file not found at: {e}",
                exit_code=EXIT_INVALID_INPUT,
            )
        except ConfigInvalidException as e:
            fatal(
                f"Invalid config:\n{e.underlying}",
                exit_code=EXIT_INVALID_INPUT,
            )
        except TestRequestFailedException as e:
            fatal(
                f"GitLab test request failed:\n{e.underlying}",
                exit_code=EXIT_PROCESSING_ERROR,
            )

        return gitlab, configuration

    def run(self) -> None:
        """
        The main method.
        """

        projects, groups = self._show_header(
            self.target,
        )

        group_number = 0
        successful_groups = 0
        failed_groups = {}

        effective_configuration = EffectiveConfigurationFile(self.output_file)

        for group in groups:
            group_number += 1

            if group_number < self.start_from_group:
                self._info_group_count(
                    "@",
                    group_number,
                    len(groups),
                    yellow,
                    f"Skipping group {group} as requested to start from {self.start_from_group}...",
                    reset,
                )
                continue

            group_configuration = self.configuration.get_effective_config_for_group(
                group
            )

            effective_configuration.add_placeholder(group)

            self._info_group_count(
                "@",
                group_number,
                len(groups),
                f"Processing group: {group}",
            )

            try:
                self.group_processors.process_entity(
                    group,
                    group_configuration,
                    dry_run=self.noop,
                    effective_configuration=effective_configuration,
                    only_sections=self.only_sections,
                )

                successful_groups += 1

            except Exception as e:
                failed_groups[group_number] = group

                trace = traceback.format_exc()
                message = (
                    f"Error occurred while processing group {group}, exception:\n\n{e}"
                )

                if self.terminate_after_error:
                    effective_configuration.write_to_file()
                    error(message)
                    debug(trace)
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    warning(message)
                    debug(trace)
            finally:
                debug(
                    f"@ ({group_number}/{len(groups)}) FINISHED Processing group: {group}"
                )

        project_number = 0
        successful_projects = 0
        failed_projects = {}

        for project_and_group in projects:
            project_number += 1

            if project_number < self.start_from:
                self._info_project_count(
                    "*",
                    project_number,
                    len(projects),
                    yellow,
                    f"Skipping project {project_and_group} as requested to start from {self.start_from}...",
                    reset,
                )
                continue

            project_configuration = self.configuration.get_effective_config_for_project(
                project_and_group
            )

            effective_configuration.add_placeholder(project_and_group)

            self._info_project_count(
                "*",
                project_number,
                len(projects),
                f"Processing project: {project_and_group}",
            )

            try:
                self.project_processors.process_entity(
                    project_and_group,
                    project_configuration,
                    dry_run=self.noop,
                    effective_configuration=effective_configuration,
                    only_sections=self.only_sections,
                )

                successful_projects += 1

            except Exception as e:
                failed_projects[project_number] = project_and_group

                trace = traceback.format_exc()
                message = f"Error occurred while processing project {project_and_group}, exception:\n\n{e}"

                if self.terminate_after_error:
                    effective_configuration.write_to_file()
                    error(message)
                    debug(trace)
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    warning(message)
                    debug(trace)
            finally:
                debug(
                    f"* ({project_number}/{len(projects)})"
                    f" FINISHED Processing project: {project_and_group}",
                )

        effective_configuration.write_to_file()

        self._show_summary(
            groups,
            projects,
            successful_groups,
            successful_projects,
            failed_groups,
            failed_projects,
        )

    @classmethod
    def _show_version(cls, skip_version_check: bool) -> None:
        """
        Prints the app version and how it relates to the latest stable version
        available at PyPI.

        :param skip_version_check: if True then the comparison to the latest versions is skipped
        """

        local_version = pkg_resources.get_distribution("gitlabform").version

        # fmt: off
        tower_crane = Symbol("🏗", "")
        to_show = [reset, tower_crane, "GitLabForm version:", blue, local_version, reset]
        # fmt: on
        message(*to_show, sep=" ", end="")

        if skip_version_check:
            # just print end of the line
            print()
        else:
            try:
                latest_version = luddite.get_version_pypi("gitlabform")
            except Exception as e:
                # end the line with current version
                print()
                error(f"Checking latest version failed:\n{e}")
                return

            if local_version == latest_version:
                # fmt: off
                happy = Symbol("😊", ":)")
                to_show = ["= the latest stable ", happy]
                # fmt: on
            elif packaging_version.parse(local_version) < packaging_version.parse(
                latest_version
            ):
                # fmt: off
                sad = Symbol("😔", ":(")
                to_show = ["= outdated ", sad, " , please update! (the latest stable is ", latest_version, ")"]
                # fmt: on
            else:
                # fmt: off
                excited = Symbol("🤩", "8)")
                to_show = ["= pre-release ", excited, " (the latest stable is ", latest_version, ")"]
                # fmt: on

            # complete the line with a line ending
            message(*to_show, sep="")

    def _show_header(
        self,
        target: str,
    ) -> Tuple[list, list]:
        """
        Gets the list of groups and projects to apply the configuration to, based on the provided 'target' parameter
        and prints out the output header based on that.

        :param target: what the configuration should be applied to
        :return: a tuple of lists of effective projects and effective groups
        """

        if target == "ALL":
            info(
                ">>> Getting ALL groups and projects that I have permission to modify..."
            )
        elif target == "ALL_DEFINED":
            info(">>> Getting ALL groups and projects DEFINED in the configuration...")
        else:
            info(">>> Getting requested groups or projects...")

        groups = self.groups_provider.get_groups(target)
        projects = self.projects_provider.get_projects(target)

        if len(groups.get_effective()) == 0 and len(projects.get_effective()) == 0:
            if target == "ALL":
                error_message = "GitLab has no projects and groups!"
            elif target == "ALL_DEFINED":
                error_message = (
                    "Configuration does not have any groups or projects defined!"
                )
            else:
                error_message = f"Project or group {target} cannot be found in GitLab!"
            fatal(
                error_message,
                exit_code=EXIT_INVALID_INPUT,
            )

        self.groups_and_projects_filters.filter(groups, projects)

        self._show_input_entities(groups)
        self._show_input_entities(projects)

        return projects.get_effective(), groups.get_effective()

    @classmethod
    def _show_input_entities(cls, entities: Entities) -> None:
        """
        Prints out the groups or projects that will be processed.

        :param entities: groups or projects
        """
        info_1(f"# of {entities.name} to process: {len(entities.get_effective())}")

        entities_omitted = ""
        entities_verbose = f"{entities.name}: {entities.get_effective()}"
        if entities.any_omitted():
            entities_omitted += f"(# of omitted {entities.name} -"
            first = True
            for reason in entities.omitted:
                if len(entities.omitted[reason]) > 0:
                    if not first:
                        entities_omitted += ","
                    entities_omitted += (
                        f" {reason.value}: {len(entities.omitted[reason])}"
                    )
                    entities_verbose += f"\nomitted {entities.name} - {reason.value}: {entities.get_omitted(reason)}"
                    first = False
            entities_omitted += ")"

        if entities_omitted:
            info_1(entities_omitted)

        verbose(entities_verbose)

    @classmethod
    def _show_summary(
        cls,
        effective_groups: list,
        effective_projects: list,
        successful_groups: int,
        successful_projects: int,
        failed_groups: dict,
        failed_projects: dict,
    ):
        """
        Prints out the summary after processing has ended with the info of what was done and what failed.

        :param effective_groups: list of effective groups that the run was done on
        :param effective_projects: list of effective projects that the run was done on
        :param successful_groups: number of successfully processed groups
        :param successful_projects: number of successfully processed projects
        :param failed_groups: a dict with failed groups, where keys are their numbers in the processing order
        :param failed_projects: a dict with failed projects, where keys are their numbers in the processing order
        """

        if len(effective_groups) > 0 or len(effective_projects) > 0:
            info_1(f"# of groups processed successfully: {successful_groups}")
            info_1(f"# of projects processed successfully: {successful_projects}")

        if len(failed_groups) > 0:
            info_1(red, f"# of groups failed: {len(failed_groups)}", reset)
            for group_number in failed_groups.keys():
                # fmt: off
                info_1(red, f"Failed group {group_number}: {failed_groups[group_number]}", reset)
                # fmt: on
        if len(failed_projects) > 0:
            # fmt: off
            info_1(red, f"# of projects failed: {len(failed_projects)}", reset)
            # fmt: on
            for project_number in failed_projects.keys():
                # fmt: off
                info_1(red, f"Failed project {project_number}: {failed_projects[project_number]}", reset)
                # fmt: on

        if len(failed_groups) > 0 or len(failed_projects) > 0:
            sys.exit(EXIT_PROCESSING_ERROR)
        elif successful_groups > 0 or successful_projects > 0:
            # fmt: off
            shine = Symbol("✨", "!!!")
            info_1(green, "All requested groups/projects processed successfully!", reset, shine)
            # fmt: on
        else:
            # fmt: off
            info_1(yellow, "Nothing to do.", reset)
            # fmt: on

    @classmethod
    def _info_group_count(
        cls, prefix, i: int, n: int, *rest: Token, **kwargs: Any
    ) -> None:
        cls._info_count(purple, prefix, i, n, *rest, **kwargs)

    @classmethod
    def _info_project_count(
        cls, prefix, i: int, n: int, *rest: Token, **kwargs: Any
    ) -> None:
        cls._info_count(green, prefix, i, n, *rest, **kwargs)

    @classmethod
    def _info_count(
        cls, color, prefix, i: int, n: int, *rest: Token, **kwargs: Any
    ) -> None:
        num_digits = len(str(n))
        counter_format = f"(%{num_digits}d/%d)"
        counter_str = counter_format % (i, n)
        info(color, prefix, reset, counter_str, reset, *rest, **kwargs)


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter,
):
    pass
