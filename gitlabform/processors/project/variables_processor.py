from cli_ui import debug
from cli_ui import warning

import copy
import textwrap
import ez_yaml

from gitlabform.gitlab import GitLab
from gitlabform.processors.util.difference_logger import hide
from gitlabform.processors.defining_keys import Key, And, OptionalKey
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class VariablesProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "variables",
            gitlab,
            list_method_name="get_variables",
            add_method_name="post_variable",
            delete_method_name="delete_variable",
            defining=And(Key("key"), OptionalKey("environment_scope")),
            required_to_create_or_update=And(Key("key"), Key("value")),
            edit_method_name="put_variable",
        )

    def _can_proceed(self, project_or_group: str, configuration: dict):
        if self.gitlab.get_project_settings(project_or_group).get("builds_access_level") == "disabled":
            warning("Builds disabled in this project so I can't set variables here.")
            return False
        else:
            return True

    def _print_diff(self, project_and_group: str, configuration, diff_only_changed: bool = False):
        try:
            current_variables = self.gitlab.get_variables(project_and_group)

            for variable in current_variables:
                variable["value"] = hide(variable["value"])

            debug(f"Variables for {project_and_group} in GitLab:")

            debug(
                textwrap.indent(
                    ez_yaml.to_string(current_variables),
                    "  ",
                )
            )
        except:
            debug(f"Variables for {project_and_group} in GitLab cannot be checked.")

        debug(f"Variables in {project_and_group} in configuration:")

        configured_variables = copy.deepcopy(configuration)

        enforce_variables = configured_variables.get("enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "variable"
        if enforce_variables:
            configured_variables.pop("enforce")

        for key in configured_variables.keys():
            configured_variables[key]["value"] = hide(configured_variables[key]["value"])

        debug(
            textwrap.indent(
                ez_yaml.to_string(configured_variables),
                "  ",
            )
        )
