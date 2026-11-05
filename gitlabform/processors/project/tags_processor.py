import sys
from logging import debug, warning, critical, error

from gitlabform.constants import EXIT_PROCESSING_ERROR
from gitlabform.gitlab import AccessLevel, GitLab
from gitlab import GitlabCreateError, GitlabDeleteError, GitlabGetError
from gitlabform.processors.abstract_processor import AbstractProcessor


class TagsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, strict: bool):
        super().__init__("tags", gitlab)
        self.strict = strict

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project = self.gl.get_project_by_path_cached(name=project_and_group, lazy=True)

        for tag in sorted(configuration["tags"]):
            try:
                if configuration["tags"][tag]["protected"]:
                    desired_state = self._get_tag_state_from_configuration(configuration["tags"][tag])

                    try:
                        previous_state = self._get_tag_state_from_gitlab(project.protectedtags.get(tag))
                    except GitlabGetError as e:
                        if e.response_code != 404:
                            raise
                        previous_state = None

                    if previous_state is not None and not self._needs_update(previous_state, desired_state):
                        debug("Tag '%s' is already protected as configured", tag)
                        continue

                    debug("Setting tag '%s' as *protected*", tag)
                    try:
                        # try to unprotect first
                        project.protectedtags.delete(tag)
                    except GitlabDeleteError:
                        pass

                    try:
                        project.protectedtags.create(self._get_create_data(tag, desired_state))
                    except GitlabCreateError:
                        if previous_state is None:
                            raise
                        warning(f"Could not protect tag '{tag}' as configured, restoring its previous protection")
                        try:
                            project.protectedtags.create(self._get_create_data(tag, previous_state))
                        except GitlabCreateError as restore_error:
                            error(f"Could not restore the previous protection of tag '{tag}': {restore_error}")
                        raise
                else:
                    debug("Setting tag '%s' as *unprotected*", tag)
                    project.protectedtags.delete(tag)
            except GitlabDeleteError:
                message = f"Tag '{tag}' not found when trying to unprotect it!"
                if self.strict:
                    critical(message)
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    warning(message)
            except GitlabGetError as e:
                if self.strict:
                    critical(
                        e,
                    )
                    sys.exit(EXIT_PROCESSING_ERROR)
                else:
                    warning(e)

    def _get_current_state(self, project_and_group: str) -> dict:
        project = self.gl.get_project_by_path_cached(name=project_and_group, lazy=True)
        return {rule.name: self._get_tag_state_from_gitlab(rule) for rule in project.protectedtags.list(get_all=True)}

    def _get_desired_state(self, entity_config: dict) -> dict:
        return {
            tag: self._get_tag_state_from_configuration(tag_config) if tag_config["protected"] else {"protected": False}
            for tag, tag_config in entity_config.items()
        }

    def _get_tag_state_from_configuration(self, tag_configuration: dict) -> dict:
        access_levels = set()
        user_ids = set()
        group_ids = set()

        for config in tag_configuration.get("allowed_to_create", []):
            if "access_level" in config:
                access_levels.add(config["access_level"])
            elif "user_id" in config:
                user_ids.add(config["user_id"])
            elif "user" in config:
                user_id = self.gl.get_user_id_cached(config["user"])
                if user_id is None:
                    error(f"Could not find User '{config["user"]}' on the Instance, cannot Protect Tag with them")
                    raise GitlabGetError(
                        f"_process_configuration - No users found when searching for username {config["user"]}",
                        404,
                    )

                user_ids.add(user_id)
            elif "group_id" in config:
                group_ids.add(config["group_id"])
            elif "group" in config:
                try:
                    gitlab_group = self.gl.get_group_by_path_cached(config["group"])
                except GitlabGetError as e:
                    error(f"Could not find Group '{config["group"]}' on the Instance, cannot Protect Tag with them")
                    raise e

                group_ids.add(gitlab_group.get_id())

        if "create_access_level" in tag_configuration:
            access_levels.add(tag_configuration["create_access_level"])

        # GitLab protects a tag for the Maintainer role when it gets no access levels
        if not (access_levels or user_ids or group_ids):
            access_levels.add(AccessLevel.MAINTAINER.value)

        return self._get_tag_state(access_levels, user_ids, group_ids, set())

    def _get_tag_state_from_gitlab(self, protected_tag) -> dict:
        access_levels = set()
        user_ids = set()
        group_ids = set()
        deploy_key_ids = set()

        for level in protected_tag.create_access_levels:
            if level.get("user_id"):
                user_ids.add(level["user_id"])
            elif level.get("group_id"):
                group_ids.add(level["group_id"])
            elif level.get("deploy_key_id"):
                deploy_key_ids.add(level["deploy_key_id"])
            else:
                access_levels.add(level["access_level"])

        return self._get_tag_state(access_levels, user_ids, group_ids, deploy_key_ids)

    @staticmethod
    def _get_tag_state(access_levels: set, user_ids: set, group_ids: set, deploy_key_ids: set) -> dict:
        return {
            "protected": True,
            "allowed_to_create": [{"access_level": value} for value in sorted(access_levels)]
            + [{"user_id": value} for value in sorted(user_ids)]
            + [{"group_id": value} for value in sorted(group_ids)]
            + [{"deploy_key_id": value} for value in sorted(deploy_key_ids)],
        }

    @staticmethod
    def _get_create_data(tag: str, tag_state: dict) -> dict:
        # GitLab CE takes a role only as create_access_level, not in allowed_to_create
        data: dict = {"name": tag, "allowed_to_create": []}
        for entry in tag_state["allowed_to_create"]:
            if "access_level" in entry and "create_access_level" not in data:
                data["create_access_level"] = entry["access_level"]
            else:
                data["allowed_to_create"].append(entry)
        return data
