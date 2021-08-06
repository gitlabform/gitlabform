import os
import logging
import textwrap

import cli_ui
import yaml
from pathlib import Path

from mergedeep import merge

from gitlabform import EXIT_INVALID_INPUT


class ConfigurationCore:

    config = None
    config_dir = None

    def __init__(self, config_path=None, config_string=None):

        if config_path and config_string:
            cli_ui.fatal(
                "Please initialize with either config_path or config_string, not both.",
                exit_code=EXIT_INVALID_INPUT,
            )

        try:
            if config_string:
                cli_ui.debug("Reading config from provided string.")
                self.config = yaml.safe_load(textwrap.dedent(config_string))
                self.config_dir = "."
            else:  # maybe config_path
                if "APP_HOME" in os.environ:
                    # using this env var should be considered unofficial, we need this temporarily
                    # for backwards compatibility. support for it may be removed without notice, do not use it!
                    config_path = os.path.join(os.environ["APP_HOME"], "config.yml")
                elif not config_path:
                    # this case is only meant for using gitlabform as a library
                    config_path = os.path.join(
                        str(Path.home()), ".gitlabform", "config.yml"
                    )
                elif config_path in [os.path.join(".", "config.yml"), "config.yml"]:
                    # provided points to config.yml in the app current working dir
                    config_path = os.path.join(os.getcwd(), "config.yml")

                cli_ui.debug(f"Reading config from file: {config_path}")

                with open(config_path, "r") as ymlfile:
                    self.config = yaml.safe_load(ymlfile)
                    logging.debug("Config parsed successfully as YAML.")

                # we need config path for accessing files for relative paths
                self.config_dir = os.path.dirname(config_path)

                if self.config.get("example_config"):
                    cli_ui.fatal(
                        "Example config detected, aborting.\n"
                        "Haven't you forgotten to use `-c <config_file>` parameter?\n"
                        "If you created your config based on the example config.yml,"
                        " then please remove 'example_config' key.",
                        exit_code=EXIT_INVALID_INPUT,
                    )

                if self.config.get("config_version", 1) != 2:
                    cli_ui.fatal(
                        "This version of GitLabForm requires 'config_version: 2' entry in the config.\n"
                        "This ensures that when the application behavior changes in a backward incompatible way,"
                        " you won't apply unexpected configuration to your GitLab instance.\n"
                        "Please read the upgrading guide here: https://bit.ly/3ub1g5C\n",
                        exit_code=EXIT_INVALID_INPUT,
                    )

                # we are NOT checking for the existence of non-empty 'projects_and_groups' key here
                # as it would break using GitLabForm as a library

        except (FileNotFoundError, IOError):
            raise ConfigFileNotFoundException(config_path)

        except Exception as e:
            raise ConfigInvalidException(e)

    def get(self, path, default=None):
        """
        :param path: "path" to given element in YAML file, for example for:

        group_settings:
          sddc:
            deploy_keys:
              qa_puppet:
                key: some key...
                title: some title...
                can_push: false

        ..a path to a single element array ['qa_puppet'] will be: "group_settings|sddc|deploy_keys".

        To get the dict under it use: get("group_settings|sddc|deploy_keys")

        :param default: the value to return if the key is not found. The default 'None' means that an exception
                        will be raised in such case.
        :return: element from YAML file (dict, array, string...)
        """
        tokens = path.split("|")
        current = self.config

        try:
            for token in tokens:
                current = current[token]
        except:
            if default is not None:
                return default
            else:
                raise KeyNotFoundException

        return current

    def get_group_config(self, group) -> dict:
        """
        :param group: group/subgroup
        :return: literal configuration for this group/subgroup or empty dict if not defined
        """
        return self.get(f"projects_and_groups|{group}/*", {})

    def get_project_config(self, group_and_project) -> dict:
        """
        :param group_and_project: 'group/project'
        :return: literal configuration for this project or empty dict if not defined
        """
        return self.get(f"projects_and_groups|{group_and_project}", {})

    def get_common_config(self) -> dict:
        """
        :return: literal common configuration or empty dict if not defined
        """
        return self.get("projects_and_groups|*", {})

    def is_project_skipped(self, project) -> bool:
        """
        :return: if project is defined in the key with projects to skip
        """
        return project in self.get("skip_projects", [])

    def is_group_skipped(self, group) -> bool:
        """
        :return: if group is defined in the key with groups to skip
        """
        return group in self.get("skip_groups", [])

    @staticmethod
    def merge_configs(more_general_config, more_specific_config) -> dict:
        """
        :return: merge more general config with more specific configs.
                 More specific config values take precedence over more general ones.
        """
        return dict(merge({}, more_general_config, more_specific_config))


class ConfigFileNotFoundException(Exception):
    pass


class ConfigInvalidException(Exception):
    def __init__(self, underlying: Exception):
        self.underlying = underlying


class KeyNotFoundException(Exception):
    pass
