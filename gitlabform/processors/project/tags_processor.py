import logging

import cli_ui

from gitlabform import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException
from gitlabform.processors.abstract_processor import AbstractProcessor


class TagsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("tags")
        self.gitlab = gitlab
        self.strict = strict

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for tag in sorted(configuration["tags"]):
            try:
                if configuration["tags"][tag]["protected"]:
                    create_access_level = (
                        configuration["tags"][tag]["create_access_level"]
                        if "create_access_level" in configuration["tags"][tag]
                        else None
                    )
                    logging.debug("Setting tag '%s' as *protected*", tag)
                    try:
                        # try to unprotect first
                        self.gitlab.unprotect_tag(project_and_group, tag)
                    except NotFoundException:
                        pass
                    self.gitlab.protect_tag(project_and_group, tag, create_access_level)
                else:
                    logging.debug("Setting tag '%s' as *unprotected*", tag)
                    self.gitlab.unprotect_tag(project_and_group, tag)
            except NotFoundException:
                message = f"Tag '{tag}' not found when trying to set it as protected/unprotected!"
                if self.strict:
                    cli_ui.fatal(
                        message,
                        exit_code=EXIT_PROCESSING_ERROR,
                    )
                else:
                    cli_ui.warning(message)
