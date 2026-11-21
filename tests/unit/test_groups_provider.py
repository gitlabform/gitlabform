from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gitlab import GitlabGetError, GitlabListError
from gitlabform.lists.groups import GroupsProvider


@pytest.fixture
def gitlab_mock():
    return MagicMock()


@pytest.fixture
def configuration_mock():
    return MagicMock()


class TestGetSingleGroup:
    def test__target_is_a_project__returns_no_groups(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_group_by_path_cached.side_effect = GitlabGetError("not found", response_code=404)

        provider = GroupsProvider(gitlab_mock, configuration_mock, recurse_subgroups=True)

        assert provider.get_groups("group/project").get_effective() == []
        gitlab_mock.get_group_descendants.assert_not_called()

    def test__non_404_error_on_the_lookup_is_raised(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_group_by_path_cached.side_effect = GitlabGetError("forbidden", response_code=403)

        provider = GroupsProvider(gitlab_mock, configuration_mock, recurse_subgroups=True)

        with pytest.raises(GitlabGetError):
            provider.get_groups("group")

    def test__error_on_the_descendants_is_not_swallowed(self, gitlab_mock, configuration_mock):
        # once the group lookup succeeded, a failing descendants call is a real error;
        # swallowing it would also skip the omission of skipped groups
        gitlab_mock.get_group_by_path_cached.return_value = SimpleNamespace(full_path="group")
        gitlab_mock.get_group_descendants.side_effect = GitlabListError("gone", response_code=404)

        provider = GroupsProvider(gitlab_mock, configuration_mock, recurse_subgroups=True)

        with pytest.raises(GitlabListError):
            provider.get_groups("group")

    def test__skipped_descendant_is_omitted(self, gitlab_mock, configuration_mock):
        gitlab_mock.get_group_by_path_cached.return_value = SimpleNamespace(full_path="group")
        gitlab_mock.get_group_descendants.return_value = [{"full_path": "group/sub"}]
        configuration_mock.is_group_skipped.side_effect = lambda group: group == "group/sub"

        provider = GroupsProvider(gitlab_mock, configuration_mock, recurse_subgroups=True)

        assert provider.get_groups("GROUP").get_effective() == ["group"]
