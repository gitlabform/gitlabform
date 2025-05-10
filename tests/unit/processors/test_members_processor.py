import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from gitlabform.processors.project.members_processor import MembersProcessor
from gitlab.v4.objects import ProjectMember, Project, User, ProjectMemberManager
from gitlabform.gitlab.python_gitlab import PythonGitlab
from gitlabform.gitlab import GitLab


class TestMembersProcessor:

    @pytest.fixture
    def gitlab_mock(self) -> GitLab:
        gitlab_mock = MagicMock()
        return gitlab_mock

    @pytest.fixture
    def processor(self, gitlab_mock: GitLab):
        processor = MembersProcessor(gitlab_mock)
        gitlab = MagicMock(GitLab)
        processor.gl = gitlab
        processor.gl.version = MagicMock(return_value=["17.1.0"])
        processor.gl.get_project_by_path_cached = MagicMock()
        return processor

    @pytest.mark.parametrize(
        "version,expected", [("17.1.0", True), ("18.0.0", True), ("16.11.0", False), ("17.0.0", False)]
    )
    def test_process_gitlab_version_for_native_members_call(self, processor: MembersProcessor, version, expected):
        assert processor._process_gitlab_version_for_native_members_call(version) == expected

    @pytest.fixture
    def project(self) -> Project:
        project = MagicMock(spec=Project)
        project.members = MagicMock()
        project.members.update = MagicMock()
        project.namespace = {"full_path": "placeholder"}
        return project

    @pytest.fixture
    def expires_at_date(self) -> datetime:
        return datetime(2025, 2, 27, 22, 6, 57)

    @pytest.fixture
    def users(self, expires_at_date) -> dict:
        return {"some_user": {"access_level": 30, "expires_at": expires_at_date, "member_role": 1}}

    @pytest.fixture
    def current_members(self, expires_at_date) -> dict[str, MagicMock]:
        member_mock = MagicMock(spec=ProjectMember)
        member_mock.access_level = 40
        member_mock.expires_at = expires_at_date.strftime("%Y-%m-%d")
        member_mock.id = 123123
        type(member_mock).member_role = PropertyMock(return_value={"id": 40})
        current_members = {"some_user": member_mock}
        return current_members

    def test_process_users_no_users(self, processor: MembersProcessor):
        with (
            patch.object(processor.gl, "get_project_by_path_cached", create=True),
            patch.object(
                processor, "_process_users_as_members", return_value=1, create=True
            ) as mock_process_users_as_members,
            patch.object(processor, "_enforce_members") as mock_enforce_members,
        ):
            processor._process_users("", {}, False, False)
            mock_process_users_as_members.assert_not_called()
            mock_enforce_members.assert_not_called()

    def test_process_users_with_defined_users(self, processor: MembersProcessor):
        with (
            patch.object(processor, "_process_users_as_members", create=True) as mock_process_users_as_members,
            patch.object(processor, "_enforce_members", create=True) as mock_enforce_members,
        ):
            processor._process_users("", {"testuser": {"expires_at"}}, False, False)
            mock_process_users_as_members.assert_called_once()
            mock_enforce_members.assert_not_called()

    def test_process_users_with_no_users_but_enforced(self, processor: MembersProcessor):
        with (
            patch.object(processor, "_process_users_as_members", create=True) as mock_process_users_as_members,
            patch.object(processor, "_enforce_members", create=True) as mock_enforce_members,
        ):
            processor._process_users("", {}, True, False)
            mock_process_users_as_members.assert_not_called()
            mock_enforce_members.assert_called_once()

    def test_process_users_as_members_native_call(self, processor: MembersProcessor, project, users, current_members):
        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=123, create=True) as mock_get_user_id_cache,
            patch.object(processor.gl, "get_member_role_id_cached", return_value=None, create=True),
        ):
            processor._process_users_as_members(users, True, project, current_members)
            mock_get_user_id_cache.assert_not_called()

    def test_process_users_as_members_no_native_call(
        self, processor: MembersProcessor, project, users, current_members
    ):
        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=123, create=True) as mock_get_user_id_cache,
            patch.object(processor.gl, "get_member_role_id_cached", return_value=1, create=True),
        ):
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id_cache.assert_called_once()
            project.members.update.assert_called_once()

    def test_process_users_as_members_no_native_call_no_user_id(
        self, processor: MembersProcessor, project, users, current_members
    ):
        with patch.object(processor.gl, "get_user_id_cached", return_value=None, create=True) as mock_get_user_id:
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id.assert_called_once()

    def test_process_users_as_members_no_native_call_with_user_id(
        self, processor: MembersProcessor, project, users, current_members
    ):
        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=1, create=True) as mock_get_user_id,
            patch.object(
                processor.gl, "get_member_role_id_cached", return_value=40, create=True
            ) as mock_get_member_role_id,
        ):
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id.assert_called_once()
            mock_get_member_role_id.assert_called_once()
            project.members.update.assert_called_once()

    def test_process_users_as_members_no_native_call_with_user_id_no_member_role(
        self, processor: MembersProcessor, project, users, current_members
    ):

        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=1, create=True) as mock_get_user_id,
            patch.object(processor.gl, "get_member_role_id_cached", return_value=1, create=True),
        ):
            users["some_user"]["member_role"] = None
            member_mock_instance = current_members["some_user"]
            type(member_mock_instance).member_role = PropertyMock(return_value={"id": None})
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id.assert_called_once()
            project.members.update.assert_called_once()

    def test_process_users_as_members_no_native_call_nothing_to_change(
        self, processor: MembersProcessor, project, users, current_members
    ):
        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=1, create=True) as mock_get_user_id,
            patch.object(processor.gl, "get_member_role_id_cached", return_value=1, create=True),
        ):
            users["some_user"]["access_level"] = 40
            users["some_user"]["member_role"] = None
            member_mock_instance = current_members["some_user"]
            type(member_mock_instance).member_role = PropertyMock(return_value={"id": None})
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id.assert_called_once()

    def test_process_users_as_members_no_native_call_no_member_role_current_member(
        self, processor: MembersProcessor, project, users, current_members
    ):
        with (
            patch.object(processor.gl, "get_user_id_cached", return_value=1, create=True) as mock_get_user_id,
            patch.object(processor.gl, "get_member_role_id_cached", return_value=1, create=True),
        ):
            member_mock = MagicMock(spec=ProjectMember)
            member_mock.access_level = 40
            member_mock.expires_at = current_members["some_user"].expires_at
            member_mock.id = 123123
            current_members["some_user"] = member_mock
            processor._process_users_as_members(users, False, project, current_members)
            mock_get_user_id.assert_called_once()
