from abc import ABC, abstractmethod

from gitlabform.configuration import Configuration

from types import SimpleNamespace
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor
from yamlpath.exceptions import YAMLPathException

from gitlabform.gitlab import AccessLevel


class ConfigurationTransformer(ABC):
    @classmethod
    @abstractmethod
    def transform(cls, configuration: Configuration):
        pass


class AccessLevelsTransformer(ConfigurationTransformer):
    """
    Internally the app supports only numeric access levels, but for user-friendliness
    this class allows providing them as strings and transforms these strings into
    the appropriate numbers.
    """

    @classmethod
    def transform(cls, configuration: Configuration):
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
            # tags
            "**.create_access_level[.!<100]",
        ]

        for path in paths_to_hashes:
            try:
                for node_coordinate in processor.get_nodes(path):
                    node_coordinate.parent[
                        node_coordinate.parentref
                    ] = AccessLevel.get_value(str(node_coordinate.node))
            except YAMLPathException:
                pass

        # there are different than the above, as they are elements of arrays
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
                        node_coordinate.parent[
                            node_coordinate.parentref
                        ] = AccessLevel.get_value(str(node_coordinate.node))
            except YAMLPathException:
                pass
