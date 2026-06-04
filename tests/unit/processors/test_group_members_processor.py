from unittest.mock import MagicMock

from gitlabform.processors.group.group_members_processor import GroupMembersProcessor


class TestGroupMembersProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.configuration = MagicMock()
        self.processor = GroupMembersProcessor(self.gitlab, self.configuration)

    def test__can_proceed__skips_inherited_group_members_for_descendant_when_ancestor_is_processed(self):
        self.configuration.has_group_section_defined_locally.return_value = False
        self.processor.set_effective_groups(["some-group", "some-group/subgroup"])

        assert self.processor._can_proceed("some-group/subgroup", {"group_members": {}}) is False

    def test__can_proceed__allows_explicit_group_members_on_descendant(self):
        self.configuration.has_group_section_defined_locally.return_value = True
        self.processor.set_effective_groups(["some-group", "some-group/subgroup"])

        assert self.processor._can_proceed("some-group/subgroup", {"group_members": {}}) is True

    def test__can_proceed__allows_descendant_when_ancestor_is_not_in_current_run(self):
        self.configuration.has_group_section_defined_locally.return_value = False
        self.processor.set_effective_groups(["some-group/subgroup"])

        assert self.processor._can_proceed("some-group/subgroup", {"group_members": {}}) is True
