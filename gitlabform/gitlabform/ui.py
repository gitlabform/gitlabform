from typing import Any

from cli_ui import info, green, reset, Token, yellow, purple


def info_group_count(prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:

    info_count(purple, prefix, i, n, *rest, **kwargs)


def info_project_count(prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:

    info_count(green, prefix, i, n, *rest, **kwargs)


def info_count(color, prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:
    num_digits = len(str(n))
    counter_format = "(%{}d/%d)".format(num_digits)
    counter_str = counter_format % (i, n)
    info(color, prefix, reset, counter_str, reset, *rest, **kwargs)
