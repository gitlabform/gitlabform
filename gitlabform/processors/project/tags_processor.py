from logging import debug
from cli_ui import warning, fatal

from gitlabform.constants import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform.processors.abstract_processor import AbstractProcessor


class TagsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("tags", gitlab)
        self.strict = strict

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for tag in sorted(configuration["tags"]):
            try:
                if configuration["tags"][tag]["protected"]:
                    allowed_to_create = []

                    if "allowed_to_create" in configuration["tags"][tag]:
                        access_levels = set()
                        user_ids = set()
                        group_ids = set()

                        requested_configuration = configuration["tags"][tag][
                            "allowed_to_create"
                        ]

                        for config in requested_configuration:
                            if "access_level" in config:
                                access_levels.add(config["access_level"])
                            elif "user_id" in config:
                                user_ids.add(config["user_id"])
                            elif "user" in config:
                                user_ids.add(self.gitlab._get_user_id(config["user"]))
                            elif "group_id" in config:
                                group_ids.add(config["group_id"])
                            elif "group" in config:
                                group_ids.add(
                                    self.gitlab._get_group_id(config["group"])
                                )

                        for val in access_levels:
                            allowed_to_create.append({"access_level": val})

                        for val in user_ids:
                            allowed_to_create.append({"user_id": val})

                        for val in group_ids:
                            allowed_to_create.append({"group_id": val})

                    create_access_level = (
                        configuration["tags"][tag]["create_access_level"]
                        if "create_access_level" in configuration["tags"][tag]
                        else None
                    )
                    debug("Setting tag '%s' as *protected*", tag)
                    try:
                        # try to unprotect first
                        self.gitlab.unprotect_tag(project_and_group, tag)
                    except NotFoundException:
                        pass
                    self.gitlab.protect_tag(
                        project_and_group, tag, allowed_to_create, create_access_level
                    )
                else:
                    debug("Setting tag '%s' as *unprotected*", tag)
                    self.gitlab.unprotect_tag(project_and_group, tag)
            except NotFoundException:
                message = f"Tag '{tag}' not found when trying to set it as protected/unprotected!"
                if self.strict:
                    fatal(
                        message,
                        exit_code=EXIT_PROCESSING_ERROR,
                    )
                else:
                    warning(message)
