from abc import ABC, abstractmethod


class AbstractKey(ABC):
    """
    This represents a key in an entity configuration.

    For example in such an entity:

    rule:
      name: foo
      rule_type: bar

    ...the "name" and "rule_type" are keys.

    This may also be an expression made with keys and relationships between them, see below.
    """

    @abstractmethod
    def matches(self, e1, e2):
        """
        :param e1: some entity
        :param e2: another entity
        :return: True if the two given entities have the same value of this key.
        """
        pass

    @abstractmethod
    def contains(self, entity):
        """
        :param entity: some entity
        :return: True if the entity contains this key
        """
        pass

    @abstractmethod
    def explain(self) -> str:
        """
        :return: a user-friendly explanation of what this key is
        """
        pass


class Key(AbstractKey):
    """
    A single, mandatory key.
    """

    def __init__(self, name):
        self.name = name

    def matches(self, e1, e2):
        return self.name in e1 and self.name in e2 and e1[self.name] == e2[self.name]

    def contains(self, entity):
        return entity.get(self.name, None) is not None

    def explain(self) -> str:
        return f"'{self.name}'"


# class KeyWithValue(AbstractKey):
#     """
#     A single, mandatory key with a specific value.
#     """
#     def __init__(self, name, value):
#         self.name = name
#         self.value = value
#
#     def matches(self, e1, e2):
#         return (
#                 self.name in e1 and self.name in e2 and e1[self.name] == e2[self.name] and e1[self.name] == self.value
#         )
#
#     def contains(self, entity):
#         return entity.get(self.name, None) == self.value
#
#     def explain(self) -> str:
#         return f"'{self.value}=={self.value}'"


class And(AbstractKey):
    """
    This groups two or more keys of which all are mandatory.
    """

    def __init__(self, *arg: AbstractKey):
        self.keys = arg

    def matches(self, e1, e2):
        return all([key.matches(e1, e2) for key in self.keys])

    def contains(self, entity):
        return all([key.contains(entity) for key in self.keys])

    def explain(self) -> str:
        explains = [key.explain() for key in self.keys]
        return f"({' and '.join(explains)})"


class Or(AbstractKey):
    """
    This groups two or more keys where at least one must exist.
    """

    def __init__(self, *arg: AbstractKey):
        self.keys = arg

    def matches(self, e1, e2):
        return any([key.matches(e1, e2) for key in self.keys])

    def contains(self, entity):
        return any([key.contains(entity) for key in self.keys])

    def explain(self) -> str:
        explains = [key.explain() for key in self.keys]
        return f"({' or '.join(explains)})"


class Xor(AbstractKey):
    """
    This groups two or more keys where exactly one must exist.
    """

    def __init__(self, *arg: AbstractKey):
        self.keys = arg

    # copied from https://stackoverflow.com/a/16801336/2693875
    @staticmethod
    def _single_true(iterable):
        iterator = iter(iterable)

        # consume from "i" until first true, or it's exhausted
        has_true = any(iterator)

        # carry on consuming until another true value / exhausted
        has_another_true = any(iterator)

        # True if exactly one true found
        return has_true and not has_another_true

    def matches(self, e1, e2):
        return self._single_true([key.matches(e1, e2) for key in self.keys])

    def contains(self, entity):
        return self._single_true([key.contains(entity) for key in self.keys])

    def explain(self) -> str:
        explains = [key.explain() for key in self.keys]
        return f"(exactly one of: {', '.join(explains)})"


class OptionalKey(AbstractKey):
    """
    This is a non-mandatory key.
    """

    def __init__(self, name):
        self.name = name

    def matches(self, e1, e2):
        only_in_e1 = self.name in e1 and self.name not in e2
        only_in_e2 = self.name not in e1 and self.name in e2
        in_both_and_equal = (
            self.name in e1 and self.name in e2 and e1[self.name] == e2[self.name]
        )
        return only_in_e1 or only_in_e2 or in_both_and_equal

    def contains(self, entity):
        # as it's optional, we don't check for its existence
        return True

    def explain(self) -> str:
        return f"(optionally '{self.name}')"
