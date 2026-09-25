from unittest.mock import MagicMock

from gitlabform.gitlab.groups import GitLabGroups


def test_get_group_excludes_projects():
    gitlab = GitLabGroups.__new__(GitLabGroups)
    gitlab._make_requests_to_api = MagicMock(return_value={})

    gitlab.get_group("parent/group")

    gitlab._make_requests_to_api.assert_called_once_with(
        "groups/%s?with_projects=false",
        "parent/group",
    )
