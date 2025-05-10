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
        processor.gl = MagicMock(spec=PythonGitlab)
        processor.gl.version.return_value = ["17.1.0"]
        return processor
    
    @pytest.mark.parametrize("version,expected", [("17.1.0", True), ("18.0.0", True), ("16.11.0", False), ("17.0.0", False)])
    def test_process_gitlab_version_for_native_members_call(self, processor: MembersProcessor, version, expected):
        assert processor._process_gitlab_version_for_native_members_call(version) == expected

    def test_process_users_no_users(self, processor: MembersProcessor):
        processor._process_users_as_members = MagicMock()
        processor._enforce_members = MagicMock()

        processor._process_users("", {}, False, False)
        processor._process_users_as_members.assert_not_called()
        processor._enforce_members.assert_not_called()


    def test_process_users_with_defined_users(self, processor: MembersProcessor):
        processor._process_users_as_members = MagicMock()
        processor._enforce_members = MagicMock()

        processor._process_users("", {"testuser": {"expires_at"}}, False, False)
        processor._process_users_as_members.assert_called_once()
        processor._enforce_members.assert_not_called()
    
    def test_process_users_with_no_users_but_enforced(self, processor: MembersProcessor):
        processor._process_users_as_members = MagicMock()
        processor._enforce_members = MagicMock()

        processor._process_users("", {}, True, False)
        processor._process_users_as_members.assert_not_called()
        processor._enforce_members.assert_called_once()
