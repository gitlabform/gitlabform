import json
from typing import Any
from urllib.error import URLError

import luddite
import pkg_resources
import sys
from cli_ui import debug as verbose
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
from packaging import version as packaging_version

from gitlabform import EXIT_PROCESSING_ERROR, EXIT_INVALID_INPUT, Entities


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
    target,
    groups_and_projects_provider,
    non_empty_configs_provider,
):
    if target == "ALL":
        info(">>> Getting ALL groups and projects...")
    elif target == "ALL_DEFINED":
        info(">>> Getting ALL_DEFINED groups and projects...")
    else:
        info(">>> Getting requested groups/projects...")

    groups, projects = groups_and_projects_provider.get_groups_and_projects(target)

    if len(groups.get_effective()) == 0 and len(projects.get_effective()) == 0:
        if target == "ALL":
            error_message = "GitLab has no projects and groups!"
        elif target == "ALL_DEFINED":
            error_message = (
                "Configuration does not have any groups or projects defined!"
            )
        else:
            error_message = f"Project or group {target} cannot be found in GitLab!"
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

    show_input_entities(groups)
    show_input_entities(projects)

    return projects.get_effective(), groups.get_effective()


def show_input_entities(entities: Entities):
    info_1(f"# of {entities.name} to process: {len(entities.get_effective())}")

    entities_omitted = ""
    entities_verbose = f"{entities.name}: {entities.get_effective()}"
    if entities.any_omitted():
        entities_omitted += f"(# of omitted {entities.name} -"
        first = True
        for reason in entities.omitted:
            if len(entities.omitted[reason]) > 0:
                if not first:
                    entities_omitted += ","
                entities_omitted += f" {reason}: {len(entities.omitted[reason])}"
                entities_verbose += f"\nomitted {entities.name} - {reason}: {entities.get_omitted(reason)}"
                first = False
        entities_omitted += ")"

    if entities_omitted:
        info_1(entities_omitted)

    verbose(entities_verbose)


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
    counter_format = f"(%{num_digits}d/%d)"
    counter_str = counter_format % (i, n)
    info(color, prefix, reset, counter_str, reset, *rest, **kwargs)


def to_str(a_dict: dict) -> str:
    # arguably the most readable form of a dict in a single line
    # is JSON with sorted keys
    return json.dumps(a_dict, sort_keys=True)
