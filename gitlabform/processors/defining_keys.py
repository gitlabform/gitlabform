class Key:
    def __init__(self, value):
        self.value = value

    def matches(self, e1, e2):
        return (
            self.value in e1 and self.value in e2 and e1[self.value] == e2[self.value]
        )

    def contains(self, entity):
        return entity.get(self.value, None) is not None

    def explain(self) -> str:
        return f"'{self.value}'"


class And(Key):
    def __init__(self, *arg: Key):
        self.keys = arg

    def matches(self, e1, e2):
        return all([key.matches(e1, e2) for key in self.keys])

    def contains(self, entity):
        return all([key.contains(entity) for key in self.keys])

    def explain(self) -> str:
        explains = [key.explain() for key in self.keys]
        return f"({' and '.join(explains)})"


class Or(Key):
    def __init__(self, *arg: Key):
        self.keys = arg

    def matches(self, e1, e2):
        return any([key.matches(e1, e2) for key in self.keys])

    def contains(self, entity):
        return any([key.contains(entity) for key in self.keys])

    def explain(self) -> str:
        explains = [key.explain() for key in self.keys]
        return f"({' or '.join(explains)})"


class Xor(Key):
    def __init__(self, *arg: Key):
        self.keys = arg

    # copied from https://stackoverflow.com/a/16801336/2693875
    @staticmethod
    def _single_true(iterable):
        iterator = iter(iterable)

        # consume from "i" until first true or it's exhausted
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
