from datetime import date
from unittest.mock import MagicMock

from gitlabform.processors.group.group_members_processor import GroupMembersProcessor


class TestGroupMembersProcessor:
    def setup_method(self):
        self.processor = GroupMembersProcessor.__new__(GroupMembersProcessor)
        self.processor.gl = MagicMock()

    def test__process_groups_formats_date_expires_at_before_sharing(self):
        group = MagicMock()
        group.shared_with_groups = []
        self.processor.gl.get_group_id.return_value = 123

        self.processor._process_groups(
            group,
            {
                "parent/child": {
                    "group_access": 30,
                    "expires_at": date(2026, 6, 18),
                }
            },
            enforce_group_members=False,
        )

        group.share.assert_called_once_with(123, 30, "2026-06-18")

    def test__process_users_formats_date_expires_at_before_creating_member(self):
        group = MagicMock()
        group.members.list.return_value = []
        self.processor.gl.get_user_id_cached.return_value = 456

        self.processor._process_users(
            {
                "Alice": {
                    "access_level": 30,
                    "expires_at": date(2026, 6, 18),
                }
            },
            enforce_group_members=False,
            keep_bots=False,
            group=group,
        )

        group.members.create.assert_called_once_with(
            {
                "user_id": 456,
                "access_level": 30,
                "expires_at": "2026-06-18",
                "member_role_id": None,
            }
        )
