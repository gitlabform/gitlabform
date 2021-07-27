import sys
from typing import Any

import cli_ui
import luddite
import pkg_resources
from packaging import version as packaging_version
from cli_ui import info, green, reset, Token, purple

from gitlabform import EXIT_PROCESSING_ERROR


def show_version(skip_version_check: bool):
    local_version = pkg_resources.get_distribution("gitlabform").version

    tower_crane = cli_ui.Symbol("🏗", "")
    tokens_to_show = [
        cli_ui.reset,
        tower_crane,
        " GitLabForm version:",
        cli_ui.blue,
        local_version,
        cli_ui.reset,
    ]

    cli_ui.message(*tokens_to_show, end="")

    if skip_version_check:
        # just print end of the line
        print()
    else:
        latest_version = luddite.get_version_pypi("gitlabform")
        if local_version == latest_version:
            happy = cli_ui.Symbol("😊", "")
            tokens_to_show = [
                "= the latest stable ",
                happy,
            ]
        elif packaging_version.parse(local_version) < packaging_version.parse(
            latest_version
        ):
            sad = cli_ui.Symbol("😔", "")
            tokens_to_show = [
                "= outdated ",
                sad,
                f", please update! (the latest stable is ",
                cli_ui.blue,
                latest_version,
                cli_ui.reset,
                ")",
            ]
        else:
            excited = cli_ui.Symbol("🤩", "")
            tokens_to_show = [
                "= pre-release ",
                excited,
                f" (the latest stable is ",
                cli_ui.blue,
                latest_version,
                cli_ui.reset,
                ")",
            ]

        cli_ui.message(*tokens_to_show, sep="")


def show_summary(
    successful_groups: int,
    successful_projects: int,
    failed_groups: dict,
    failed_projects: dict,
):
    cli_ui.info_1(f"# of groups processed successfully: {successful_groups}")
    cli_ui.info_1(f"# of projects processed successfully: {successful_projects}")

    if len(failed_groups) > 0:
        cli_ui.info_1(
            cli_ui.red, f"# of groups failed: {len(failed_groups)}", cli_ui.reset
        )
        for group_number in failed_groups.keys():
            cli_ui.info_1(
                cli_ui.red,
                f"Failed group {group_number}: {failed_groups[group_number]}",
                cli_ui.reset,
            )
    if len(failed_projects) > 0:
        cli_ui.info_1(
            cli_ui.red,
            f"# of projects failed: {len(failed_projects)}",
            cli_ui.reset,
        )
        for project_number in failed_projects.keys():
            cli_ui.info_1(
                cli_ui.red,
                f"Failed project {project_number}: {failed_projects[project_number]}",
                cli_ui.reset,
            )

    if len(failed_groups) > 0 or len(failed_projects) > 0:
        sys.exit(EXIT_PROCESSING_ERROR)
    elif successful_groups > 0 or successful_projects > 0:
        shine = cli_ui.Symbol("✨", "!!!")
        cli_ui.info_1(
            cli_ui.green,
            f"All requested groups/projects processes successfully!",
            cli_ui.reset,
            shine,
        )


def info_group_count(prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:
    info_count(purple, prefix, i, n, *rest, **kwargs)


def info_project_count(prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:
    info_count(green, prefix, i, n, *rest, **kwargs)


def info_count(color, prefix, i: int, n: int, *rest: Token, **kwargs: Any) -> None:
    num_digits = len(str(n))
    counter_format = "(%{}d/%d)".format(num_digits)
    counter_str = counter_format % (i, n)
    info(color, prefix, reset, counter_str, reset, *rest, **kwargs)
