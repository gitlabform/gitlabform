import argparse
import logging.config
import sys
import traceback

import luddite
import pkg_resources
from typing import TextIO

from gitlabform.configuration import Configuration
from gitlabform.configuration.core import ConfigFileNotFoundException
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform.gitlab.core import TestRequestFailedException
from gitlabform.gitlabform.processors.group import GroupProcessors
from gitlabform.gitlabform.processors.project import ProjectProcessors


class GitLabFormCore(object):
    def __init__(self, project_or_group=None, config_string=None):

        if project_or_group and config_string:
            self.project_or_group = project_or_group
            self.config_string = config_string
            self.verbose = False
            self.debug = True
            self.strict = True
            self.start_from = 1
            self.noop = False
            self.output_file = (None,)
            self.set_log_level(tests=True)
            self.skip_version_check = True
            self.skip_archived_projects = False
            self.show_version = False
            self.terminate_after_error = True
        else:
            (
                self.project_or_group,
                self.config,
                self.verbose,
                self.debug,
                self.strict,
                self.start_from,
                self.noop,
                self.output_file,
                self.skip_version_check,
                self.show_version,
                self.terminate_after_error,
                self.skip_archived_projects,
            ) = self.parse_args()
            self.set_log_level()

            print(self.get_version(self.skip_version_check))
            if self.show_version:
                sys.exit(0)

            if not self.project_or_group:
                print("project_or_group parameter is required.")
                sys.exit(1)

        self.gl, self.c = self.initialize_configuration_and_gitlab()

        self.group_processors = GroupProcessors(self.gl)
        self.project_processors = ProjectProcessors(self.gl, self.c, self.strict)

    def parse_args(self):

        parser = argparse.ArgumentParser(
            description='Specialized "configuration as a code" tool for GitLab projects, groups and more'
            " using hierarchical configuration written in YAML",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
            "-c", "--config", default="config.yml", help="Config file path and filename"
        )

        group_ex = parser.add_mutually_exclusive_group()

        group_ex.add_argument(
            "-v", "--verbose", action="store_true", help="Verbose mode"
        )

        group_ex.add_argument(
            "-d", "--debug", action="store_true", help="Debug mode (most verbose)"
        )

        parser.add_argument(
            "--strict",
            "-s",
            action="store_true",
            help="Stop on missing branches and tags",
        )

        parser.add_argument(
            "--start-from",
            dest="start_from",
            default=1,
            type=int,
            help="Start processing projects from the given one "
            '(as numbered by "[x/y] Processing: group/project" messages)',
        )

        parser.add_argument(
            "-n",
            "--noop",
            dest="noop",
            action="store_true",
            help="Run in no-op (dry run) mode",
        )

        parser.add_argument(
            "-o",
            "--output-file",
            dest="output_file",
            default=None,
            help="name/path of a file to write the effective configs to",
        )

        parser.add_argument(
            "-V",
            "--version",
            dest="show_version",
            action="store_true",
            help="Show the version and exit",
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
            help="Terminates the program from running after the first error",
        )

        parser.add_argument(
            "-i",
            "--skip-archived-projects",
            dest="skip_archived_projects",
            action="store_true",
            help="Skips the configuration of projects that have been archived",
        )

        args = parser.parse_args()

        return (
            args.project_or_group,
            args.config,
            args.verbose,
            args.debug,
            args.strict,
            args.start_from,
            args.noop,
            args.output_file,
            args.skip_version_check,
            args.show_version,
            args.terminate_after_error,
            args.skip_archived_projects,
        )

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

    def get_version(self, skip_version_check):
        local_version = pkg_resources.get_distribution("gitlabform").version
        version = f"GitLabForm version: {local_version}"

        if not skip_version_check:
            latest_version = luddite.get_version_pypi("gitlabform")
            if local_version == latest_version:
                version += " (the latest)"
            else:
                version += f" (the latest is {latest_version} - please update!)"

        return version

    def initialize_configuration_and_gitlab(self):

        try:
            if hasattr(self, "config_string"):
                gl = GitLab(config_string=self.config_string)
                c = Configuration(config_string=self.config_string)
            else:
                gl = GitLab(self.config.strip())
                c = Configuration(self.config.strip())
            return gl, c
        except ConfigFileNotFoundException as e:
            logging.fatal("Aborting - config file not found at: %s", e)
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
            logging.warning(">>> Processing ALL groups and and projects")
            groups = self.gl.get_groups()
        elif self.project_or_group == "ALL_DEFINED":
            logging.warning(">>> Processing ALL groups and projects defined in config")
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
            for project in self.gl.get_projects(
                group, ignore_archived=self.skip_archived_projects
            ):
                projects_and_groups.add(project)
        projects_and_groups = sorted(list(projects_and_groups))

        # skip projects after getting projects from gitlab
        if self.c.get_skip_projects():
            effective_projects_and_groups = [
                x for x in projects_and_groups if x not in self.c.get_skip_projects()
            ]
        else:
            effective_projects_and_groups = projects_and_groups

        logging.warning("*** # of groups to process: %s", str(len(groups)))
        logging.warning(
            "*** # of projects to process: %s", str(len(effective_projects_and_groups))
        )

        return effective_projects_and_groups, effective_groups

    def process_all(self, projects_and_groups, groups):

        g = 0

        maybe_output_file = self.try_to_get_output_file()

        for group in groups:

            g += 1

            configuration = self.c.get_effective_config_for_group(group)

            if configuration:
                logging.warning("> (%s/%s) Processing: %s", g, len(groups), group)

                if self.noop:
                    logging.debug(
                        "Configuration that would be applied: %s" % str(configuration)
                    )

                self.try_to_write_header_to_output_file(group, maybe_output_file)

                try:
                    self.group_processors.process_group(
                        group,
                        configuration,
                        dry_run=self.noop,
                        output_file=maybe_output_file,
                    )

                except Exception as e:
                    if self.terminate_after_error:
                        self.try_to_close_output_file(maybe_output_file)
                        print(
                            "+++ Errors occurred while processing due to '%s' ... Exiting now...",
                            e,
                        )
                        sys.exit(1)
                    logging.error("+++ Error while processing '%s'", group)
                    traceback.print_exc()
                finally:
                    logging.debug(
                        "< (%s/%s) FINISHED Processing: %s", g, len(groups), group
                    )

            else:
                self.try_to_write_header_to_output_file(
                    group, maybe_output_file, empty_config=True
                )

                logging.warning(
                    "> (%s/%s) Skipping group %s as it has empty effective config.",
                    g,
                    len(groups),
                    group,
                )

        p = 0

        for project_and_group in projects_and_groups:

            p += 1

            if p < self.start_from:
                logging.warning(
                    "$$$ [%s/%s] Skipping: %s...",
                    p,
                    len(projects_and_groups),
                    project_and_group,
                )
                continue

            configuration = self.c.get_effective_config_for_project(project_and_group)

            if configuration:
                logging.warning(
                    "* [%s/%s] Processing: %s",
                    p,
                    len(projects_and_groups),
                    project_and_group,
                )

                if self.noop:
                    logging.debug(
                        "Configuration that would be applied: %s" % str(configuration)
                    )

                self.try_to_write_header_to_output_file(
                    project_and_group, maybe_output_file
                )

                try:
                    self.project_processors.process_project(
                        project_and_group,
                        configuration,
                        dry_run=self.noop,
                        output_file=maybe_output_file,
                    )

                except Exception as e:
                    if self.terminate_after_error:
                        self.try_to_close_output_file(maybe_output_file)
                        print(
                            "+++ Errors occurred while processing due to '%s' ... Exiting now...",
                            e,
                        )
                        sys.exit(1)
                    logging.error("+++ Error while processing '%s'", project_and_group)
                    traceback.print_exc()
                finally:
                    logging.debug(
                        "@ [%s/%s] FINISHED Processing: %s",
                        p,
                        len(projects_and_groups),
                        project_and_group,
                    )
            else:
                self.try_to_write_header_to_output_file(
                    project_and_group, maybe_output_file, empty_config=True
                )
                logging.warning(
                    "* [%s/%s] Skipping project %s as it has empty effective config.",
                    p,
                    len(projects_and_groups),
                    project_and_group,
                )

    def try_to_get_output_file(self):
        if self.output_file:
            try:
                output_file = open(self.output_file, "w")
                logging.debug(
                    f"Opened file {self.output_file} to write the effective configs to."
                )
                return output_file
            except Exception as e:
                logging.error(
                    f"Error when trying to open {self.output_file} write the effective configs to: {e}"
                )
                sys.exit(2)
        else:
            return None

    def try_to_write_header_to_output_file(
        self,
        project_or_project_and_group: str,
        output_file: TextIO,
        empty_config: bool = False,
    ):
        """
        Writes a shared key for the "_write_to_file" method which actually dumps the configurations.
        """
        if output_file:
            try:
                if empty_config:
                    output_file.writelines(f"{project_or_project_and_group}: {{}}\n")
                else:
                    output_file.writelines(f"{project_or_project_and_group}:\n")
            except Exception as e:
                logging.error(f"Error when trying to write to {output_file.name}: {e}")
                raise e

    def try_to_close_output_file(self, output_file: TextIO):
        if output_file:
            try:
                output_file.close()
                logging.debug(f"Closed file {self.output_file}.")
            except Exception as e:
                logging.error(f"Error when trying to close {self.output_file}: {e}")
                sys.exit(3)
