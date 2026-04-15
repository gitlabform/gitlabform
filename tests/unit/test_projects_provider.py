from unittest.mock import MagicMock

import pytest

from gitlabform.gitlab.core import NotFoundException
from gitlabform.lists import OmissionReason, Groups
from gitlabform.lists.projects import ProjectsProvider


@pytest.fixture
def gitlab_mock():
    return MagicMock()


@pytest.fixture
def configuration_mock():
    return MagicMock()


def make_provider(gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=True):
    return ProjectsProvider(
        gitlab_mock,
        configuration_mock,
        include_archived,
        include_scheduled_for_deletion,
        recurse_subgroups=True,
    )


class TestGetAllAndOmittedProjectsFromGroups:
    def test__both_flags_true__returns_only_names(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = ["group/project1", "group/project2"]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=True
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        gitlab_mock.get_projects.assert_called_once_with("group", include_archived=True)
        assert sorted(all_projects) == ["group/project1", "group/project2"]
        assert archived == []
        assert scheduled == []

    def test__exclude_archived__returns_archived_separately(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": None},
            {"path_with_namespace": "group/project2", "archived": True, "marked_for_deletion_on": None},
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=False, include_scheduled_for_deletion=True
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        gitlab_mock.get_projects.assert_called_once_with("group", include_archived=True, only_names=False)
        assert sorted(all_projects) == ["group/project1", "group/project2"]
        assert archived == ["group/project2"]
        assert scheduled == []

    def test__exclude_scheduled_for_deletion__returns_scheduled_separately(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": None},
            {"path_with_namespace": "group/project2", "archived": False, "marked_for_deletion_on": "2026-04-15"},
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=False
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        gitlab_mock.get_projects.assert_called_once_with("group", include_archived=True, only_names=False)
        assert sorted(all_projects) == ["group/project1", "group/project2"]
        assert archived == []
        assert scheduled == ["group/project2"]

    def test__exclude_both__returns_both_separately(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": None},
            {"path_with_namespace": "group/project2", "archived": True, "marked_for_deletion_on": None},
            {"path_with_namespace": "group/project3", "archived": False, "marked_for_deletion_on": "2026-04-15"},
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=False, include_scheduled_for_deletion=False
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        assert sorted(all_projects) == ["group/project1", "group/project2", "group/project3"]
        assert archived == ["group/project2"]
        assert scheduled == ["group/project3"]

    def test__project_both_archived_and_scheduled__appears_in_both_lists(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": True, "marked_for_deletion_on": "2026-04-15"},
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=False, include_scheduled_for_deletion=False
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        assert all_projects == ["group/project1"]
        assert archived == ["group/project1"]
        assert scheduled == ["group/project1"]

    def test__marked_for_deletion_on_null__not_scheduled(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": None},
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=False
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(["group"])

        assert all_projects == ["group/project1"]
        assert scheduled == []

    def test__deduplicates_across_groups(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.side_effect = [
            [
                {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": "2026-04-15"},
            ],
            [
                {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": "2026-04-15"},
            ],
        ]

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=False
        )
        all_projects, archived, scheduled = provider._get_all_and_omitted_projects_from_groups(
            ["group", "group/subgroup"]
        )

        assert all_projects == ["group/project1"]
        assert scheduled == ["group/project1"]


class TestVerifyIfProjectsExistAndGetOmittedProjects:
    def test__normal_project__not_omitted(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": False,
            "marked_for_deletion_on": None,
        }

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=False, include_scheduled_for_deletion=False
        )
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == []
        assert scheduled == []

    def test__archived_project__omitted_when_flag_false(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": True,
            "marked_for_deletion_on": None,
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_archived=False)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == ["group/project1"]
        assert scheduled == []

    def test__archived_project__not_omitted_when_flag_true(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": True,
            "marked_for_deletion_on": None,
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_archived=True)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == []
        assert scheduled == []

    def test__scheduled_for_deletion_project__omitted_when_flag_false(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": False,
            "marked_for_deletion_on": "2026-04-15",
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_scheduled_for_deletion=False)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == []
        assert scheduled == ["group/project1"]

    def test__scheduled_for_deletion_project__not_omitted_when_flag_true(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": False,
            "marked_for_deletion_on": "2026-04-15",
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_scheduled_for_deletion=True)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == []
        assert scheduled == []

    def test__both_archived_and_scheduled__in_both_lists_when_flags_false(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": True,
            "marked_for_deletion_on": "2026-04-15",
        }

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=False, include_scheduled_for_deletion=False
        )
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["group/project1"])

        assert archived == ["group/project1"]
        assert scheduled == ["group/project1"]

    def test__transfer_source_scheduled_for_deletion__omitted_when_flag_false(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.side_effect = [
            NotFoundException("not found at target path"),
            {
                "path_with_namespace": "old_group/project1",
                "archived": False,
                "marked_for_deletion_on": "2026-04-15",
            },
        ]
        configuration_mock.config = {
            "projects_and_groups": {
                "new_group/project1": {"project": {"transfer_from": "old_group/project1"}},
            }
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_scheduled_for_deletion=False)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["new_group/project1"])

        assert archived == []
        assert scheduled == ["new_group/project1"]

    def test__transfer_source_scheduled_for_deletion__not_omitted_when_flag_true(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_project_case_insensitive.side_effect = [
            NotFoundException("not found at target path"),
            {
                "path_with_namespace": "old_group/project1",
                "archived": False,
                "marked_for_deletion_on": "2026-04-15",
            },
        ]
        configuration_mock.config = {
            "projects_and_groups": {
                "new_group/project1": {"project": {"transfer_from": "old_group/project1"}},
            }
        }

        provider = make_provider(gitlab_mock, configuration_mock, include_scheduled_for_deletion=True)
        archived, scheduled = provider._verify_if_projects_exist_and_get_omitted_projects(["new_group/project1"])

        assert archived == []
        assert scheduled == []


class TestGetProjects:
    def _make_groups(self, effective):
        groups = Groups()
        groups.add_requested(effective)
        return groups

    def test__scheduled_for_deletion_added_to_omitted_from_groups(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = [
            {"path_with_namespace": "group/project1", "archived": False, "marked_for_deletion_on": None},
            {"path_with_namespace": "group/project2", "archived": False, "marked_for_deletion_on": "2026-04-15"},
        ]
        configuration_mock.get_projects.return_value = []
        configuration_mock.is_project_skipped.return_value = False

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=False
        )
        groups = self._make_groups(["group"])

        projects = provider._get_projects("ALL", groups)

        assert "group/project1" in projects.get_effective()
        assert "group/project2" not in projects.get_effective()
        assert projects.get_omitted(OmissionReason.SCHEDULED_FOR_DELETION) == ["group/project2"]

    def test__all_defined__scheduled_for_deletion_from_configuration(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_projects.return_value = []
        gitlab_mock.get_project_case_insensitive.return_value = {
            "path_with_namespace": "group/project1",
            "archived": False,
            "marked_for_deletion_on": "2026-04-15",
        }
        configuration_mock.get_projects.return_value = ["group/project1"]
        configuration_mock.is_project_skipped.return_value = False

        provider = make_provider(
            gitlab_mock, configuration_mock, include_archived=True, include_scheduled_for_deletion=False
        )
        groups = self._make_groups([])

        projects = provider._get_projects("ALL_DEFINED", groups)

        assert projects.get_omitted(OmissionReason.SCHEDULED_FOR_DELETION) == ["group/project1"]
        assert "group/project1" not in projects.get_effective()
