import enum

import copy
from collections import defaultdict

from typing import DefaultDict

from abc import ABC

from enum import Enum


@enum.unique
class OmissionReason(Enum):
    ARCHIVED = "archived"
    EMPTY = "empty effective config"
    SKIPPED = "skipped"


class Entities(ABC):
    """
    Entities here are lists of GitLab groups or projects on which GitLabForm will operate.
    The code here assumes that there is a set of requested entities, but some of them may be omitted for various reasons
    so there effective set of entities may be different.
    """

    def __init__(self, name: str):
        self.requested: set = set()
        self.omitted: DefaultDict[OmissionReason, set] = defaultdict(set)
        self.name = name

    def add_requested(self, more_requested: list) -> None:
        self.requested = self.requested | set(more_requested)

    def add_omitted(self, reason: OmissionReason, more_omitted: list) -> None:
        self.omitted[reason] = self.omitted[reason] | set(more_omitted)

    def get_omitted(self, reason: OmissionReason) -> list:
        return sorted(self.omitted[reason])

    def any_omitted(self) -> bool:
        for reason in self.omitted:
            if len(self.omitted[reason]) > 0:
                return True
        return False

    def get_effective(self) -> list:
        effective_set = copy.deepcopy(self.requested)
        for reason in self.omitted:
            effective_set -= self.omitted[reason]
        return sorted(effective_set)


class Groups(Entities):
    def __init__(self):
        super().__init__("groups")


class Projects(Entities):
    def __init__(self):
        super().__init__("projects")
