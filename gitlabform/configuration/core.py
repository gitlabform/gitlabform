from typing import Any

import os
import logging
import textwrap
from abc import ABC
from copy import deepcopy
from logging import debug
from pathlib import Path
from ruamel.yaml.scalarstring import ScalarString
from types import SimpleNamespace

from cli_ui import debug as verbose
from cli_ui import fatal
from mergedeep import merge
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter

from gitlabform.constants import EXIT_INVALID_INPUT
from ruamel.yaml.comments import CommentedMap


class ConfigurationCore(ABC):
    """
    The functionality shared by various types of config (common, groups, projects)
    is implemented here.
    """

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

                if self.config.get("config_version", 1) != 3:
                    fatal(
                        "This version of GitLabForm requires 'config_version: 3' entry in the config. "
                        "This ensures that if the application behavior changes in a backward-incompatible way,"
                        " you won't apply unwanted configuration to your GitLab instance.\n"
                        "Please follow this guide: https://gitlabform.github.io/gitlabform/upgrade/\n",
                        exit_code=EXIT_INVALID_INPUT,
                    )

            self._find_almost_duplicates()

            # we are NOT checking for the existence of non-empty 'projects_and_groups' key here
            # as it would break using GitLabForm as a library

        except (FileNotFoundError, OSError):
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
            config = textwrap.dedent(source)
            verbose("Reading config from the provided string.")
            (yaml_data, doc_loaded) = Parsers.get_yaml_data(
                yaml, log, config, literal=True
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

    def get(self, path, default=None) -> Any:
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

            if isinstance(current, ScalarString):
                to_return = str(current)
            else:
                to_return = current
        except:
            if default is not None:
                to_return = default
            else:
                raise KeyNotFoundException(path) from None

        return to_return

    @staticmethod
    def _validate_break_inheritance_flag(
        config: dict, section_name: str, parent_key: str = ""
    ) -> None:
        for key, value in config.items():
            if "inherit" == key:
                parent_key_description = (
                    ' under key "' + parent_key + '"' if parent_key else ""
                )
                fatal(
                    f'The inheritance-break flag set in "{section_name}"{parent_key_description} is invalid\n'
                    f"because it has no higher level setting to inherit from.\n",
                    exit_code=EXIT_INVALID_INPUT,
                )
            elif type(value) in [CommentedMap, dict]:
                ConfigurationCore._validate_break_inheritance_flag(
                    value, section_name, key
                )

    @staticmethod
    def _merge_configs(more_general_config, more_specific_config) -> dict:
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
                elif type(value) in [CommentedMap, dict]:
                    break_inheritance(value, key)

        def replace_config_sections(merged_config, specific_key, specific_config):
            for key, value in merged_config.items():
                if specific_key == key:
                    del specific_config["inherit"]
                    merged_config[key] = specific_config
                    break
                elif type(value) in [CommentedMap, dict]:
                    replace_config_sections(value, specific_key, specific_config)

        break_inheritance(more_specific_config)

        return dict(merged_dict)

    @staticmethod
    def _get_case_insensitively(a_dict: dict, a_key: str):
        for dict_key in a_dict.keys():
            if dict_key.lower() == a_key.lower():
                return a_dict[dict_key]
        return {}

    @staticmethod
    def _is_skipped_case_insensitively(an_array: list, item: str) -> bool:
        """
        :return: if item is defined in the list to be skipped
        """
        item = item.lower()

        for list_element in an_array:
            list_element = list_element.lower()

            if list_element == item:
                return True

            if (
                list_element.endswith("/*")
                and item.startswith(list_element[:-2])
                and len(item) >= len(list_element[:-2])
            ):
                return True

        return False

    def _find_almost_duplicates(self):
        # in GitLab groups and projects names are de facto case insensitive:
        # you can change the case of both name and path BUT you cannot create
        # 2 groups which names differ only with case and the same thing for
        # projects. therefore we cannot allow such entries in the config,
        # as they would be ambiguous.

        for path in [
            "projects_and_groups",
            "skip_groups",
            "skip_projects",
        ]:
            if self.get(path, 0):
                almost_duplicates = self._find_almost_duplicates_in(path)
                if almost_duplicates:
                    fatal(
                        f"There are almost duplicates in the keys of {path} - they differ only in case.\n"
                        f"They are: {', '.join(almost_duplicates)}\n"
                        f"This is not allowed as we ignore the case for group and project names.",
                        exit_code=EXIT_INVALID_INPUT,
                    )

    def _find_almost_duplicates_in(self, configuration_path):
        """
        Checks given configuration key and reads its keys - if it is a dict - or elements - if it is a list.
        Looks for items that are almost the same - they differ only in the case.
        :param configuration_path: configuration path, f.e. "group_settings"
        :return: list of items that have almost duplicates,
                 or an empty list if none are found
        """

        dict_or_list = self.get(configuration_path)
        if isinstance(dict_or_list, dict):
            items = dict_or_list.keys()
        else:
            items = dict_or_list

        items_with_lowercase_names = [x.lower() for x in items]

        # casting these to sets will deduplicate the one with lowercase names
        # lowering its cardinality if there were elements in it
        # that before lowering differed only in case
        if len(set(items)) != len(set(items_with_lowercase_names)):
            # we have some almost duplicates, let's find them
            almost_duplicates = []
            for first_item in items:
                occurrences = 0
                for second_item in items_with_lowercase_names:
                    if first_item.lower() == second_item.lower():
                        occurrences += 1
                        if occurrences == 2:
                            almost_duplicates.append(first_item)
                            break
            return almost_duplicates

        else:
            return []


class ConfigFileNotFoundException(Exception):
    pass


class ConfigInvalidException(Exception):
    def __init__(self, underlying: Exception):
        self.underlying = underlying


class KeyNotFoundException(Exception):
    __slots__ = "key"

    def __init__(self, key: str):
        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            self.key = key
        else:
            fatal(
                f"Unable to find the key: {key.replace('|', '.')}\n",
                exit_code=EXIT_INVALID_INPUT,
            )
