import pytest
from gitlab import GitlabGetError

from gitlabform.gitlab.python_gitlab import PythonGitlab
from unittest.mock import MagicMock


class TestPythonGitlab:

    def test_get_member_roles_cached_uses_correct_path_for_saas(self):
        group_id = 2
        python_gitlab = PythonGitlab()
        # Don't make a real HTTP call
        python_gitlab.http_get = MagicMock(return_value=None)

        # Return we are in GitLab SaaS
        python_gitlab.is_gitlab_saas = MagicMock(return_value=True)

        python_gitlab.get_member_roles_cached(group_id)

        python_gitlab.http_get.assert_called_with(f"/groups/{group_id}/member_roles")

    def test_get_member_roles_cached_throws_404_error_when_invoked_on_saas_without_group_id(
        self,
    ):
        python_gitlab = PythonGitlab()
        # Don't make a real HTTP call
        python_gitlab.http_get = MagicMock(return_value=None)

        # Return we are in GitLab SaaS
        python_gitlab.is_gitlab_saas = MagicMock(return_value=True)

        with pytest.raises(GitlabGetError) as exception:
            python_gitlab.get_member_roles_cached(None)

        assert exception.value.error_message is not None
        assert exception.value.response_code == 404
        python_gitlab.http_get.assert_not_called()

    def test_get_member_roles_cached_uses_correct_path_for_self_managed_and_dedicated(
        self,
    ):
        group_id = 2
        python_gitlab = PythonGitlab()
        # Don't make a real HTTP call
        python_gitlab.http_get = MagicMock(return_value=None)

        # Return we are not in GitLab SaaS
        python_gitlab.is_gitlab_saas = MagicMock(return_value=False)

        python_gitlab.get_member_roles_cached(group_id)

        python_gitlab.http_get.assert_called_with(f"/member_roles")
