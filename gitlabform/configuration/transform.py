import logging
from abc import ABC, abstractmethod
from types import SimpleNamespace

from cli_ui import fatal
from ruamel.yaml.comments import CommentedMap
from yamlpath import Processor
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter

from gitlabform.constants import EXIT_INVALID_INPUT
from gitlabform.configuration import Configuration
from gitlabform.gitlab import AccessLevel
from gitlabform.gitlab import GitLab


class ConfigurationTransformer(ABC):
    @classmethod
    @abstractmethod
    def transform(cls, configuration: Configuration, gitlab: GitLab) -> None:
        pass


class UserTransformer(ConfigurationTransformer):
    @classmethod
    def transform(cls, configuration: Configuration, gitlab: GitLab) -> None:
        logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)

        processor = Processor(ConsolePrinter(logging_args), configuration.config)

        paths_to_user = [
            "projects_and_groups.*.protected_environments.*.deploy_access_levels.user"
        ]

        for path in paths_to_user:
            try:
                for node_coordinate in processor.get_nodes(path):
                    user = node_coordinate.parent.pop("user")

                    node_coordinate.parent["user_id"] = gitlab._get_user_id(user)
            except YAMLPathException as e:
                logging.debug(f"The YAMl library threw an exception: {e}")

                pass


class ImplicitNameTransformer(ConfigurationTransformer):
    """
    Creates a 'name' field that has the same value as the "scope" delimiter, e.g.:

    ...
      blah: # start of the cfg scope
       name: blah # name to be used
       smth_else: <...>

    It's redundant, so this can be done as :

    ...
     foo: # a 'name' field will be created as -> name: foo
       smth_else: <...>
    """

    @classmethod
    def transform(cls, configuration: Configuration, gitlab: GitLab) -> None:
        logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)

        processor = Processor(ConsolePrinter(logging_args), configuration.config)

        paths_to_implicit_names = ["projects_and_groups.*.protected_environments.*"]

        for path in paths_to_implicit_names:
            try:
                for node_coordinate in processor.get_nodes(path):
                    if not isinstance(node_coordinate.node, CommentedMap):
                        continue

                    node_coordinate.parent[node_coordinate.parentref][
                        "name"
                    ] = node_coordinate.parentref
            except YAMLPathException as e:
                logging.debug(f"The YAMl library threw an exception: {e}")

                pass


class AccessLevelsTransformer(ConfigurationTransformer):
    """
    Internally the app supports only numeric access levels, but for user-friendliness
    this class allows providing them as strings and transforms these strings into
    the appropriate numbers.
    """

    @classmethod
    def transform(cls, configuration: Configuration, gitlab: GitLab):
        logging_args = SimpleNamespace(quiet=False, verbose=False, debug=False)
        log = ConsolePrinter(logging_args)

        processor = Processor(log, configuration.config)

        # [.!<100] effectively means that the value is non-numerical
        paths_to_hashes = [
            # # branches, old syntax
            "**.push_access_level[.!<100]",
            "**.merge_access_level[.!<100]",
            "**.unprotect_access_level[.!<100]",
            # members & group members
            "**.access_level[.!<100]",
            "**.group_access[.!<100]",
            # old syntax
            "**.group_access_level[.!<100]",
            # tags
            "**.create_access_level[.!<100]",
        ]

        for path in paths_to_hashes:
            try:
                for node_coordinate in processor.get_nodes(path):
                    try:
                        access_level_string = str(node_coordinate.node)
                        node_coordinate.parent[
                            node_coordinate.parentref
                        ] = AccessLevel.get_value(access_level_string)
                    except KeyError:
                        fatal(
                            f"Configuration string '{access_level_string}' is not one of the valid access levels:"
                            f" {', '.join(AccessLevel.get_canonical_names())}",
                            exit_code=EXIT_INVALID_INPUT,
                        )
            except YAMLPathException:
                pass

        # these are different from the above, as they are elements of arrays,
        # so we need different search query and an extra condition for
        # transformation
        paths_to_arrays = [
            # # branches, new GitLab Premium syntax
            "**.allowed_to_push.*.[access_level!<100]",
            "**.allowed_to_merge.*.[access_level!<100]",
            "**.allowed_to_unprotect.*.[access_level!<100]",
        ]

        for path in paths_to_arrays:
            try:
                for node_coordinate in processor.get_nodes(path):
                    if node_coordinate.parentref == "access_level":
                        try:
                            access_level_string = str(node_coordinate.node)
                            node_coordinate.parent[
                                node_coordinate.parentref
                            ] = AccessLevel.get_value(access_level_string)
                        except KeyError:
                            fatal(
                                f"Configuration string '{access_level_string}' is not one of the valid access levels:"
                                f" {', '.join(AccessLevel.get_canonical_names())}",
                                exit_code=EXIT_INVALID_INPUT,
                            )
            except YAMLPathException:
                pass
