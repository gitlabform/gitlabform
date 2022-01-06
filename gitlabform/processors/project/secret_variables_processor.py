from cli_ui import debug as verbose
from cli_ui import warning

import copy
import textwrap
import ez_yaml

from gitlabform.gitlab import GitLab
from gitlabform.processors.util.difference_logger import hide
from gitlabform.processors.defining_keys import Key, And
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class SecretVariablesProcessor(MultipleEntitiesProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__(
            "secret_variables",
            gitlab,
            list_method_name="get_secret_variables",
            add_method_name="post_secret_variable",
            delete_method_name="delete_secret_variable",
            defining=Key("key"),
            required_to_create_or_update=And(Key("key"), Key("value")),
            edit_method_name="put_secret_variable",
        )

    def _can_proceed(self, project_or_group: str, configuration: dict):
        if (
            self.gitlab.get_project_settings(project_or_group).get(
                "builds_access_level"
            )
            == "disabled"
        ):
            warning(
                "Builds disabled in this project so I can't set secret variables here."
            )
            return False
        else:
            return True

    def _print_diff(self, project_and_group: str, configuration):

        try:
            current_secret_variables = self.gitlab.get_secret_variables(
                project_and_group
            )

            for secret_variable in current_secret_variables:
                secret_variable["value"] = hide(secret_variable["value"])

            verbose(f"Secret variables for {project_and_group} in GitLab:")

            verbose(
                textwrap.indent(
                    ez_yaml.to_string(current_secret_variables),
                    "  ",
                )
            )
        except:
            verbose(
                f"Secret variables for {project_and_group} in GitLab cannot be checked."
            )

        verbose(f"Secret variables in {project_and_group} in configuration:")

        configured_secret_variables = copy.deepcopy(configuration)
        for key in configured_secret_variables.keys():
            configured_secret_variables[key]["value"] = hide(
                configured_secret_variables[key]["value"]
            )

        verbose(
            textwrap.indent(
                ez_yaml.to_string(configured_secret_variables),
                "  ",
            )
        )
