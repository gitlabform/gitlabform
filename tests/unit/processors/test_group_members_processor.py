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

    def test__process_groups_shares_group_with_custom_role(self):
        group = MagicMock()
        group.encoded_id = "parent%2Ftarget"
        group.full_path = "parent/target"
        group.shared_with_groups = []
        self.processor.gl.get_group_id.return_value = 123
        self.processor.gl.get_member_role_id_cached.return_value = 42

        self.processor._process_groups(
            group,
            {
                "parent/invited": {
                    "group_access": 20,
                    "member_role": "Read only",
                }
            },
            enforce_group_members=False,
        )

        self.processor.gl.get_member_role_id_cached.assert_called_once_with("Read only", "parent/target")
        group.manager.gitlab.http_post.assert_called_once_with(
            "/groups/parent%2Ftarget/share",
            post_data={
                "group_id": 123,
                "group_access": 20,
                "expires_at": None,
                "member_role_id": 42,
            },
        )

    def test__process_groups_does_not_recreate_unchanged_custom_role_share(self):
        group = MagicMock()
        group.full_path = "parent/target"
        group.shared_with_groups = [
            {
                "group_id": 123,
                "group_full_path": "parent/invited",
                "group_access_level": 20,
                "expires_at": None,
                "member_role_id": 42,
            }
        ]
        self.processor.gl.get_member_role_id_cached.return_value = 42

        self.processor._process_groups(
            group,
            {
                "parent/invited": {
                    "group_access": 20,
                    "member_role": 42,
                }
            },
            enforce_group_members=False,
        )

        group.unshare.assert_not_called()
        group.share.assert_not_called()
        group.manager.gitlab.http_post.assert_not_called()

    def test__process_groups_recreates_share_when_custom_role_changes(self):
        group = MagicMock()
        group.encoded_id = "parent%2Ftarget"
        group.full_path = "parent/target"
        group.shared_with_groups = [
            {
                "group_id": 123,
                "group_full_path": "parent/invited",
                "group_access_level": 20,
                "expires_at": None,
                "member_role_id": 41,
            }
        ]
        self.processor.gl.get_member_role_id_cached.return_value = 42

        self.processor._process_groups(
            group,
            {
                "parent/invited": {
                    "group_access": 20,
                    "member_role": 42,
                }
            },
            enforce_group_members=False,
        )

        group.unshare.assert_called_once_with(123)
        group.manager.gitlab.http_post.assert_called_once_with(
            "/groups/parent%2Ftarget/share",
            post_data={
                "group_id": 123,
                "group_access": 20,
                "expires_at": None,
                "member_role_id": 42,
            },
        )

    def test__process_groups_recreates_share_without_custom_role_when_removed_from_config(self):
        group = MagicMock()
        group.full_path = "parent/target"
        group.shared_with_groups = [
            {
                "group_id": 123,
                "group_full_path": "parent/invited",
                "group_access_level": 20,
                "expires_at": None,
                "member_role_id": 42,
            }
        ]

        self.processor._process_groups(
            group,
            {
                "parent/invited": {
                    "group_access": 20,
                }
            },
            enforce_group_members=False,
        )

        group.unshare.assert_called_once_with(123)
        group.share.assert_called_once_with(123, 20, None)
        group.manager.gitlab.http_post.assert_not_called()

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
