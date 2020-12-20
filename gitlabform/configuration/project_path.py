from typing import Tuple
import re

import typing


class ProjectPath:
    __ALL_PROJECTS_PATTERN = "*"
    __ALL_PERSONAL_PROJECTS_PATTERN = "<all-users>"
    __REGEX_PREFIX = "~"
    __PROJECT_GROUP_SEPARATOR = "/"

    __ALL_MATCH_REGEX_PATTERN: typing.Pattern = re.compile(".*")

    def __init__(self, pattern: str):
        self.constant_prefix, self.regex_pattern = self.__split_into_constant_and_regex(
            pattern
        )

    def __split_into_constant_and_regex(
        self, pattern: str
    ) -> Tuple[str, typing.Pattern]:
        if pattern == self.__ALL_PROJECTS_PATTERN:
            return "", self.__ALL_MATCH_REGEX_PATTERN

        regex_start_index = pattern.find(self.__REGEX_PREFIX)
        if regex_start_index >= 0:
            regex_pattern = re.compile(pattern[regex_start_index + 1 :])
            constant_prefix = pattern[:regex_start_index]
        else:
            regex_pattern = self.__ALL_MATCH_REGEX_PATTERN
            constant_prefix = pattern

        return constant_prefix, regex_pattern

    def is_all_personal_projects_pattern(self) -> bool:
        return (
            self.constant_prefix == self.__ALL_PERSONAL_PROJECTS_PATTERN
            and self.regex_pattern == self.__ALL_MATCH_REGEX_PATTERN
        )

    def matches_path(self, path: str) -> bool:
        if (
            not self.constant_prefix
            and self.regex_pattern == self.__ALL_MATCH_REGEX_PATTERN
        ):
            return True

        if not path.startswith(self.constant_prefix):
            return False

        path_suffix = path[len(self.constant_prefix) :]
        return re.fullmatch(self.regex_pattern, path_suffix) is not None
