import pytest
from gitlab import GitlabGetError, GitlabListError

from gitlabform.gitlab.core import NotFoundException
from gitlabform.gitlab.python_gitlab import PythonGitlab
from gitlabform.gitlab import GitlabWrapper, GitLab
from unittest.mock import MagicMock, patch


class TestPythonGitlab:

    @staticmethod
    def _group(full_path: str) -> MagicMock:
        group = MagicMock()
        group.full_path = full_path
        group.asdict.return_value = {"full_path": full_path}
        return group

    @staticmethod
    def _project(path_with_namespace: str) -> MagicMock:
        project = MagicMock()
        project.path_with_namespace = path_with_namespace
        project.asdict.return_value = {"path_with_namespace": path_with_namespace}
        return project

    # ------------------------------------------------- case-insensitive lookups

    def test_get_group_case_insensitive_with_exact_case(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab.groups.get = MagicMock(return_value=self._group("Group/Sub"))

        assert python_gitlab.get_group_case_insensitive("Group/Sub") == {"full_path": "Group/Sub"}
        python_gitlab.groups.get.assert_called_once_with("Group/Sub", with_projects=False)

    def test_get_group_case_insensitive_falls_back_to_search(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab.groups.get = MagicMock(side_effect=GitlabGetError("404 Not Found", response_code=404))
        python_gitlab.groups.list = MagicMock(return_value=[self._group("Other"), self._group("Group/Sub")])

        assert python_gitlab.get_group_case_insensitive("group/SUB") == {"full_path": "Group/Sub"}
        python_gitlab.groups.list.assert_called_once_with(search="group/sub", get_all=True)

    def test_get_group_case_insensitive_not_found(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab.groups.get = MagicMock(side_effect=GitlabGetError("404 Not Found", response_code=404))
        python_gitlab.groups.list = MagicMock(return_value=[])

        with pytest.raises(NotFoundException):
            python_gitlab.get_group_case_insensitive("no/such/group")

    def test_get_project_case_insensitive_falls_back_to_search(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab.projects.get = MagicMock(side_effect=GitlabGetError("404 Not Found", response_code=404))
        python_gitlab.projects.list = MagicMock(return_value=[self._project("Group/Project")])

        assert python_gitlab.get_project_case_insensitive("group/project") == {"path_with_namespace": "Group/Project"}
        python_gitlab.projects.list.assert_called_once_with(search="group/project", get_all=True)

    def test_get_project_case_insensitive_not_found(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab.projects.get = MagicMock(side_effect=GitlabGetError("404 Not Found", response_code=404))
        python_gitlab.projects.list = MagicMock(return_value=[])

        with pytest.raises(NotFoundException):
            python_gitlab.get_project_case_insensitive("no/such/project")

    # ------------------------------------------------------- groups & projects

    def test_get_groups_as_admin_gets_all_available(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab._is_admin = MagicMock(return_value=True)
        python_gitlab.groups.list = MagicMock(return_value=[self._group("b"), self._group("a")])

        assert python_gitlab.get_groups() == ["a", "b"]
        python_gitlab.groups.list.assert_called_once_with(get_all=True, all_available=True)

    def test_get_groups_as_non_admin_requires_reporter_access(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab._is_admin = MagicMock(return_value=False)
        python_gitlab.groups.list = MagicMock(return_value=[self._group("a")])

        assert python_gitlab.get_groups() == ["a"]
        python_gitlab.groups.list.assert_called_once_with(get_all=True, min_access_level=20)

    def test_get_projects_filters_to_group_namespace_and_sorts(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab._is_admin = MagicMock(return_value=False)
        group = MagicMock()
        python_gitlab.groups.get = MagicMock(return_value=group)
        group.projects.list.return_value = [
            self._project("group/b"),
            self._project("group/a"),
            # shared with the group, but in another namespace
            self._project("other/shared"),
        ]

        assert python_gitlab.get_projects("group") == ["group/a", "group/b"]
        group.projects.list.assert_called_once_with(
            get_all=True, include_subgroups=True, archived=False, min_access_level=20
        )

    def test_get_projects_can_return_whole_project_dicts(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab._is_admin = MagicMock(return_value=False)
        group = MagicMock()
        python_gitlab.groups.get = MagicMock(return_value=group)
        group.projects.list.return_value = [self._project("group/a")]

        assert python_gitlab.get_projects("group", include_archived=True, only_names=False) == [
            {"path_with_namespace": "group/a"}
        ]
        group.projects.list.assert_called_once_with(get_all=True, include_subgroups=True, min_access_level=20)

    def test_get_projects_returns_empty_list_when_group_not_found(self):
        python_gitlab = PythonGitlab(MagicMock())
        python_gitlab._is_admin = MagicMock(return_value=False)
        group = MagicMock()
        python_gitlab.groups.get = MagicMock(return_value=group)
        group.projects.list.side_effect = GitlabListError("404 Not Found", response_code=404)

        assert python_gitlab.get_projects("no/such/group") == []

    def test_get_group_by_path_cached_excludes_projects(self):
        python_gitlab = PythonGitlab(MagicMock())
        group = MagicMock()
        python_gitlab.groups.get = MagicMock(return_value=group)

        assert python_gitlab.get_group_by_path_cached("parent/group") is group
        python_gitlab.groups.get.assert_called_once_with("parent/group", with_projects=False)

    def test_get_member_role_id_cached_gets_role_id_from_roles_in_group_on_saas(self):
        group_name = "Test"
        role_name = "custom_role"
        member_role_id = "1"

        python_gitlab = PythonGitlab(MagicMock())
        # Don't make a real GraphQl call
        python_gitlab._get_member_roles_from_group_cached = MagicMock(
            return_value=[dict(id=member_role_id, name=role_name)]
        )

        # Return we are in GitLab SaaS
        python_gitlab._is_gitlab_saas = MagicMock(return_value=True)

        role_id = python_gitlab.get_member_role_id_cached(role_name, group_name)

        python_gitlab._get_member_roles_from_group_cached.assert_called_with(group_name)
        assert role_id == int(member_role_id)

    def test_get_member_role_id_cached_gets_role_id_from_roles_on_instance_on_self_hosted(
        self,
    ):
        group_name = "Test"
        role_name = "custom_role_two"
        member_role_id = "5"

        python_gitlab = PythonGitlab(MagicMock())
        # Don't make a real GraphQl call
        python_gitlab._get_member_roles_from_instance_cached = MagicMock(
            return_value=[dict(id=member_role_id, name=role_name)]
        )

        # Return we are in GitLab SaaS
        python_gitlab._is_gitlab_saas = MagicMock(return_value=False)

        role_id = python_gitlab.get_member_role_id_cached(role_name, group_name)

        python_gitlab._get_member_roles_from_instance_cached.assert_called()
        assert role_id == int(member_role_id)

    def test_convert_result_to_member_roles_removes_GitlabGraphQl_specific_prefix_from_member_role_id(
        self,
    ):
        role_name = "custom_role"
        member_role_id = "1"

        member_role_id_prefix = "gid://gitlab/MemberRole/"

        member_role_nodes = [dict(id=f"{member_role_id_prefix}{member_role_id}", name=role_name)]

        python_gitlab = PythonGitlab(MagicMock())

        member_roles = python_gitlab._convert_result_to_member_roles(member_role_nodes)

        expected = [dict(id=member_role_id, name=role_name)]
        assert member_roles == expected


class TestGitlabWrapperExtraKwargs:
    """
    Tests for GitlabWrapper kwargs filtering.
    Ensures that only valid parameters are passed to python-gitlab's Gitlab client
    and GraphQL client, preventing TypeError from unsupported kwargs.
    """

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_max_retries_not_passed_to_gitlab_client(self, mock_python_gitlab, mock_graphql):
        """Test that max_retries is NOT passed to PythonGitlab (would cause TypeError)"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,  # This should NOT be passed to PythonGitlab
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert "max_retries" not in call_kwargs

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_max_retries_passed_to_graphql_client(self, mock_python_gitlab, mock_graphql):
        """Test that max_retries IS passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_graphql.call_args.kwargs
        assert call_kwargs["max_retries"] == 5

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_only_valid_gitlab_client_params_passed(self, mock_python_gitlab, mock_graphql):
        """Test that only valid Gitlab client parameters are passed"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "ssl_verify": True,
            "timeout": 10,
            "max_retries": 5,  # GraphQL only
            "obey_rate_limit": True,  # GraphQL only
            "some_unknown_param": "value",  # Should be filtered out
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs

        # Valid params should be present
        assert call_kwargs["url"] == "https://gitlab.example.com"
        assert call_kwargs["private_token"] == "test-token"
        assert call_kwargs["ssl_verify"] is True
        assert call_kwargs["timeout"] == 10

        # Invalid params should NOT be present
        assert "max_retries" not in call_kwargs
        assert "obey_rate_limit" not in call_kwargs
        assert "some_unknown_param" not in call_kwargs

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_graphql_params_passed_correctly(self, mock_python_gitlab, mock_graphql):
        """Test that GraphQL-specific parameters are passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "max_retries": 5,
            "obey_rate_limit": False,
            "retry_transient_errors": True,
            "timeout": 30,
            "ssl_verify": False,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_graphql.call_args.kwargs

        assert call_kwargs["max_retries"] == 5
        assert call_kwargs["obey_rate_limit"] is False
        assert call_kwargs["retry_transient_errors"] is True
        assert call_kwargs["timeout"] == 30
        assert call_kwargs["ssl_verify"] is False

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_token_renamed_to_private_token(self, mock_python_gitlab, mock_graphql):
        """Test that 'token' config key is renamed to 'private_token' for Gitlab client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "my-secret-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs

        assert "token" not in call_kwargs
        assert call_kwargs["private_token"] == "my-secret-token"

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_retry_transient_errors_default_true(self, mock_python_gitlab, mock_graphql):
        """Test that retry_transient_errors defaults to True for Gitlab client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert call_kwargs["retry_transient_errors"] is True

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_retry_transient_errors_can_be_overridden(self, mock_python_gitlab, mock_graphql):
        """Test that retry_transient_errors can be overridden from config"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
            "retry_transient_errors": False,
        }

        _ = GitlabWrapper(mock_gitlab)

        call_kwargs = mock_python_gitlab.call_args.kwargs
        assert call_kwargs["retry_transient_errors"] is False

    @patch("gitlabform.gitlab.GraphQL")
    @patch("gitlabform.gitlab.PythonGitlab")
    def test_graphql_url_and_token_passed(self, mock_python_gitlab, mock_graphql):
        """Test that URL and token are passed to GraphQL client"""
        mock_gitlab = MagicMock(spec=GitLab)
        mock_gitlab.session = MagicMock()
        mock_gitlab.gitlab_config = {
            "url": "https://gitlab.example.com",
            "token": "test-token",
        }

        _ = GitlabWrapper(mock_gitlab)

        mock_graphql.assert_called_once()
        call_args = mock_graphql.call_args
        assert call_args.kwargs["url"] == "https://gitlab.example.com"
        assert call_args.kwargs["token"] == "test-token"
