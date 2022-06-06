import os
import textwrap
from abc import ABC
from copy import deepcopy
from logging import debug
from pathlib import Path
from types import SimpleNamespace

from cli_ui import debug as verbose
from cli_ui import fatal
from mergedeep import merge
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter

from gitlabform import EXIT_INVALID_INPUT
from ruamel.yaml.comments import CommentedMap


class ConfigurationCore(ABC):
    def __init__(self, config_path=None, config_string=None):

        if config_path and config_string:
            fatal(
                "Please initialize with either config_path or config_string, not both.",
                exit_code=EXIT_INVALID_INPUT,
            )
        try:
            if config_string:
                self.config = self._parse_yaml(config_string, config_string=True)
                self.config_dir = "."
            else:  # maybe config_path
                config_path = self._get_config_path(config_path)
                self.config = self._parse_yaml(config_path, config_string=False)
                self.config_dir = os.path.dirname(config_path)

                # below checks are only needed in the non-test mode, when the config is read from file

                if self.config.get("example_config"):
                    fatal(
                        "Example config detected, aborting.\n"
                        "Haven't you forgotten to use `-c <config_file>` parameter?\n"
                        "If you created your config based on the example config.yml,"
                        " then please remove 'example_config' key.",
                        exit_code=EXIT_INVALID_INPUT,
                    )

                if self.config.get("config_version", 1) != 2:
                    fatal(
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

    @staticmethod
    def _get_config_path(config_path):

        if "APP_HOME" in os.environ:
            # using this env var should be considered unofficial, we need this temporarily
            # for backwards compatibility. support for it may be removed without notice, do not use it!
            config_path = os.path.join(os.environ["APP_HOME"], "config.yml")
        elif not config_path:
            # this case is only meant for using gitlabform as a library
            config_path = os.path.join(str(Path.home()), ".gitlabform", "config.yml")
        elif config_path in [os.path.join(".", "config.yml"), "config.yml"]:
            # provided points to config.yml in the app current working dir
            config_path = os.path.join(os.getcwd(), "config.yml")

        return config_path

    @staticmethod
    def _parse_yaml(source: str, config_string: bool):

        logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)
        log = ConsolePrinter(logging_args)

        yaml = Parsers.get_yaml_editor()

        # for better backward compatibility with PyYAML (that supports only YAML 1.1) used in the previous
        # GitLabForm versions, let's force ruamel.yaml to use YAML version 1.1 by default too
        yaml.version = (1, 1)

        if config_string:
            config_string = textwrap.dedent(source)
            verbose("Reading config from the provided string.")
            (yaml_data, doc_loaded) = Parsers.get_yaml_data(
                yaml, log, config_string, literal=True
            )
        else:
            config_path = source
            verbose(f"Reading config from file: {config_path}")
            (yaml_data, doc_loaded) = Parsers.get_yaml_data(yaml, log, config_path)

        if doc_loaded:
            debug("Config parsed successfully as YAML.")
        else:
            # an error message has already been printed via ConsolePrinter
            exit(EXIT_INVALID_INPUT)

        return yaml_data

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
        pass

    def get_project_config(self, group_and_project) -> dict:
        pass

    def get_common_config(self) -> dict:
        """
        :return: literal common configuration or empty dict if not defined
        """
        return self.get("projects_and_groups|*", {})

    def is_project_skipped(self, project) -> bool:
        pass

    def is_group_skipped(self, group) -> bool:
        pass

    def is_skipped(self, an_array: list, item: str) -> bool:
        pass

    @staticmethod
    def validate_break_inheritance_flag(config, level):
        for key, value in config.items():
            if "inherit" == key:
                fatal(
                    f"The inheritance break flag cannot be placed at the {level} level\n"
                    f"because {level} level is the highest level in the configuration file.\n",
                    exit_code=EXIT_INVALID_INPUT,
                )
                break
            elif type(value) is CommentedMap:
                ConfigurationCore.validate_break_inheritance_flag(value, level)

    @staticmethod
    def merge_configs(more_general_config, more_specific_config) -> dict:
        """
        :return: merge more general config with more specific configs.
                 More specific config values take precedence over more general ones.
        """

        more_general_config = deepcopy(more_general_config)
        more_specific_config = deepcopy(more_specific_config)

        merged_dict = merge({}, more_general_config, more_specific_config)

        def break_inheritance(specific_config, parent_key=""):
            for key, value in specific_config.items():
                if "inherit" == key:
                    if not value:
                        replace_config_sections(
                            merged_dict, parent_key, specific_config
                        )
                        break
                    elif value:
                        fatal(
                            f"Cannot set the inheritance break flag with true\n",
                            exit_code=EXIT_INVALID_INPUT,
                        )
                elif type(value) is CommentedMap:
                    break_inheritance(value, key)

        def replace_config_sections(merged_config, specific_key, specific_config):
            for key, value in merged_config.items():
                if specific_key == key:
                    del specific_config["inherit"]
                    merged_config[key] = specific_config
                    break
                elif type(value) is CommentedMap:
                    replace_config_sections(value, specific_key, specific_config)

        break_inheritance(more_specific_config)

        return dict(merged_dict)


class ConfigFileNotFoundException(Exception):
    pass


class ConfigInvalidException(Exception):
    def __init__(self, underlying: Exception):
        self.underlying = underlying


class KeyNotFoundException(Exception):
    pass
