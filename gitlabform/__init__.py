from collections import defaultdict
from typing import DefaultDict

from abc import ABC

EXIT_INVALID_INPUT = 1
EXIT_PROCESSING_ERROR = 2


class Entities(ABC):
    def __init__(self, name: str):
        self.requested: set = set()
        self.omitted: DefaultDict[str, set] = defaultdict(set)
        self.effective: list = []
        self.recalculate_effective = True
        self.name = name

    def add_requested(self, more_requested: list):
        self.requested = self.requested | set(more_requested)
        self.recalculate_effective = True

    def add_omitted(self, reason: str, more_omitted: list):
        self.omitted[reason] = self.omitted[reason] | set(more_omitted)
        self.recalculate_effective = True

    def get_omitted(self, reason: str) -> list:
        return sorted(self.omitted[reason])

    def any_omitted(self) -> bool:
        for reason in self.omitted:
            if len(self.omitted[reason]) > 0:
                return True
        return False

    def get_effective(self) -> list:
        if self.recalculate_effective:
            self.effective = self.requested
            for reason in self.omitted:
                self.effective = self.effective - self.omitted[reason]
            self.effective = sorted(self.effective)
        return self.effective


class Groups(Entities):
    def __init__(self):
        super().__init__("groups")


class Projects(Entities):
    def __init__(self):
        super().__init__("projects")
