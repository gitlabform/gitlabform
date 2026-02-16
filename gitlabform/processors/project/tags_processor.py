from logging import debug
from cli_ui import warning, fatal

from gitlabform.constants import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import GitLab
from gitlab import GitlabDeleteError, GitlabGetError
from gitlabform.processors.abstract_processor import AbstractProcessor


class TagsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("tags", gitlab)
        self.strict = strict

    def _process_configuration(self, project_or_project_and_group: str, configuration: dict):
        project = self.gl.get_project_by_path_cached(name=project_or_project_and_group, lazy=True)

        for tag in sorted(configuration["tags"]):
            try:
                if configuration["tags"][tag]["protected"]:
                    allowed_to_create = []

                    if "allowed_to_create" in configuration["tags"][tag]:
                        access_levels = set()
                        user_ids = set()
                        group_ids = set()

                        requested_configuration = configuration["tags"][tag]["allowed_to_create"]

                        for config in requested_configuration:
                            if "access_level" in config:
                                access_levels.add(config["access_level"])
                            elif "user_id" in config:
                                user_ids.add(config["user_id"])
                            elif "group_id" in config:
                                group_ids.add(config["group_id"])

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
                        project.protectedtags.delete(tag)
                    except GitlabDeleteError:
                        pass

                    data = {}
                    data["name"] = tag
                    if allowed_to_create is not None:
                        data["allowed_to_create"] = allowed_to_create
                    if create_access_level is not None:
                        data["create_access_level"] = create_access_level
                    project.protectedtags.create(data)
                else:
                    debug("Setting tag '%s' as *unprotected*", tag)
                    project.protectedtags.delete(tag)
            except GitlabDeleteError:
                message = f"Tag '{tag}' not found when trying to unprotect it!"
                if self.strict:
                    fatal(
                        message,
                        exit_code=EXIT_PROCESSING_ERROR,
                    )
                else:
                    warning(message)
            except GitlabGetError as e:
                if self.strict:
                    fatal(
                        e,
                        exit_code=EXIT_PROCESSING_ERROR,
                    )
                else:
                    warning(message)
