import sys
from typing import Any

import luddite
import pkg_resources
from cli_ui import (
    message,
    info,
    info_1,
    error,
    fatal,
    reset,
    green,
    purple,
    blue,
    red,
    yellow,
    Symbol,
    Token,
)
from cli_ui import debug as verbose

from packaging import version as packaging_version
from urllib.error import URLError

from gitlabform import EXIT_PROCESSING_ERROR, EXIT_INVALID_INPUT


def show_version(skip_version_check: bool):
    local_version = pkg_resources.get_distribution("gitlabform").version

    tower_crane = Symbol("🏗", "")
    tokens_to_show = [
        reset,
        tower_crane,
        " GitLabForm version:",
        blue,
        local_version,
        reset,
    ]

    message(*tokens_to_show, end="")

    if skip_version_check:
        # just print end of the line
        print()
    else:
        try:
            latest_version = luddite.get_version_pypi("gitlabform")
        except URLError as e:
            # end the line with current version
            print()
            error(f"Checking latest version failed:\n{e}")
            return

        if local_version == latest_version:
            happy = Symbol("😊", "")
            tokens_to_show = [
                "= the latest stable ",
                happy,
            ]
        elif packaging_version.parse(local_version) < packaging_version.parse(
            latest_version
        ):
            sad = Symbol("😔", "")
            tokens_to_show = [
                "= outdated ",
                sad,
                f", please update! (the latest stable is ",
                blue,
                latest_version,
                reset,
                ")",
            ]
        else:
            excited = Symbol("🤩", "")
            tokens_to_show = [
                "= pre-release ",
                excited,
                f" (the latest stable is ",
                blue,
                latest_version,
                reset,
                ")",
            ]

        message(*tokens_to_show, sep="")


def show_header(
    project_or_group,
    groups_and_projects_provider,
    non_empty_configs_provider,
):
    if project_or_group == "ALL":
        info(">>> Getting ALL groups and projects...")
    elif project_or_group == "ALL_DEFINED":
        info(">>> Getting ALL_DEFINED groups and projects...")
    else:
        info(">>> Getting requested groups/projects...")

    groups, projects = groups_and_projects_provider.get_groups_and_projects(
        project_or_group
    )

    if len(groups.get_effective()) == 0 and len(projects.get_effective()) == 0:
        if project_or_group == "ALL":
            error_message = "GitLab has no projects and groups!"
        elif project_or_group == "ALL_DEFINED":
            error_message = (
                "Configuration does not have any groups or projects defined!"
            )
        else:
            error_message = f"Entity {project_or_group} cannot be found in GitLab!"
        fatal(
            error_message,
            exit_code=EXIT_INVALID_INPUT,
        )

    (
        groups,
        projects,
    ) = non_empty_configs_provider.omit_groups_and_projects_with_empty_configs(
        groups, projects
    )

    groups_info = f"# of groups to process: {len(groups.get_effective())}"
    groups_verbose = f"groups: {groups.get_effective()}"

    if groups.any_omitted():
        groups_info += "\n(# of omitted groups:"
        first = True
        for reason in groups.omitted:
            if len(groups.omitted[reason]) > 0:
                if not first:
                    groups_info += ","
                groups_info += f" {reason} - {len(groups.omitted[reason])}"
                groups_verbose += (
                    f"\nomitted groups - {reason}: {groups.get_omitted(reason)}"
                )
                first = False
        groups_info += ")"

    info_1(groups_info)
    verbose(groups_verbose)

    projects_info = f"# of projects to process: {len(projects.get_effective())}"
    projects_verbose = f"projects: {projects.get_effective()}"

    if projects.any_omitted():
        projects_info += "\n(# of omitted projects:"
        first = True
        for reason in projects.omitted:
            if len(projects.omitted[reason]) > 0:
                if not first:
                    projects_info += ","
                projects_info += f" {reason} - {len(projects.omitted[reason])}"
                projects_verbose += (
                    f"\nomitted projects - {reason}: {projects.get_omitted(reason)}"
                )
            first = False
        projects_info += ")"

    info_1(projects_info)
    verbose(projects_verbose)

    return projects.get_effective(), groups.get_effective()


def show_summary(
    groups_with_non_empty_configs: list,
    projects_with_non_empty_configs: list,
    successful_groups: int,
    successful_projects: int,
    failed_groups: dict,
    failed_projects: dict,
):
    if (
        len(groups_with_non_empty_configs) > 0
        or len(projects_with_non_empty_configs) > 0
    ):
        info_1(f"# of groups processed successfully: {successful_groups}")
        info_1(f"# of projects processed successfully: {successful_projects}")

    if len(failed_groups) > 0:
        info_1(red, f"# of groups failed: {len(failed_groups)}", reset)
        for group_number in failed_groups.keys():
            info_1(
                red,
                f"Failed group {group_number}: {failed_groups[group_number]}",
                reset,
            )
    if len(failed_projects) > 0:
        info_1(
            red,
            f"# of projects failed: {len(failed_projects)}",
            reset,
        )
        for project_number in failed_projects.keys():
            info_1(
                red,
                f"Failed project {project_number}: {failed_projects[project_number]}",
                reset,
            )

    if len(failed_groups) > 0 or len(failed_projects) > 0:
        sys.exit(EXIT_PROCESSING_ERROR)
    elif successful_groups > 0 or successful_projects > 0:
        shine = Symbol("✨", "!!!")
        info_1(
            green,
            f"All requested groups/projects processed successfully!",
            reset,
            shine,
        )
    else:
        info_1(
            yellow,
            "Nothing to do.",
            reset,
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
