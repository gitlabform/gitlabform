from logging import debug
from typing import Any, cast

from gitlab.v4.objects.groups import Group

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor


class GroupMergeRequestsApprovalsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_merge_requests_approvals", gitlab)

    def _get_current_state(self, group: str) -> dict:
        gitlab_group: Group = self.gl.get_group_by_path_cached(group)
        return self._get_group_merge_requests_approvals(gitlab_group)

    def _process_configuration(self, group: str, configuration: dict) -> None:
        settings_in_config: dict = configuration.get("group_merge_requests_approvals", {})

        gitlab_group: Group = self.gl.get_group_by_path_cached(group)
        settings_in_gitlab = self._get_group_merge_requests_approvals(gitlab_group)

        debug(settings_in_gitlab)
        debug("group_merge_requests_approvals BEFORE: ^^^")

        if self._needs_update(settings_in_gitlab, settings_in_config):
            debug(f"Updating group merge requests approvals settings for group {group}")
            self._update_group_merge_requests_approvals(gitlab_group, settings_in_config)
        else:
            debug("No update needed for group merge requests approvals settings")

    def _get_group_merge_requests_approvals(self, gitlab_group: Group) -> dict:
        # TODO: python-gitlab has no manager for the /groups/:id/merge_request_approval_setting
        # endpoint yet
        settings = cast(dict[str, Any], self.gl.http_get(self._api_path(gitlab_group)))
        return self._unwrap_values(settings)

    def _update_group_merge_requests_approvals(self, gitlab_group: Group, settings: dict) -> None:
        updated_settings = cast(dict[str, Any], self.gl.http_put(self._api_path(gitlab_group), post_data=settings))

        debug(self._unwrap_values(updated_settings))
        debug("group_merge_requests_approvals AFTER: ^^^")

    @staticmethod
    def _api_path(gitlab_group: Group) -> str:
        return f"/groups/{gitlab_group.id}/merge_request_approval_setting"

    @staticmethod
    def _unwrap_values(settings: dict) -> dict:
        """Flatten GitLab's response to plain values. This API returns every setting as an object
        with the `value`, `locked` and `inherited_from` keys (both on GET and on PUT), while in the
        config the values are set directly. Without this nothing would ever compare as equal, so we
        would re-apply the settings on every run and print the raw objects in the dry-run diff."""
        return {key: setting["value"] for key, setting in settings.items()}
