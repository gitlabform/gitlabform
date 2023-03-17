import pytest

from tests.acceptance import allowed_codes, run_gitlabform
from gitlabform.gitlab import AccessLevel
from gitlabform.constants import APPROVAL_RULE_NAME

#
# TODO: remove this file in v4.x
#

pytestmark = pytest.mark.requires_license


@pytest.fixture(scope="function")
def group_with_one_owner_and_two_developers(other_group, root_user, users):
    other_group.members.create(
        {"user_id": users[0].id, "access_level": AccessLevel.OWNER.value}
    )
    other_group.members.create(
        {"user_id": users[1].id, "access_level": AccessLevel.DEVELOPER.value}
    )
    other_group.members.create(
        {"user_id": users[2].id, "access_level": AccessLevel.DEVELOPER.value}
    )
    other_group.members.delete(root_user.id)

    yield other_group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    other_group.members.create(
        {"user_id": root_user.id, "access_level": AccessLevel.OWNER.value}
    )

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        with allowed_codes(404):
            other_group.members.delete(user.id)


@pytest.fixture(scope="function")
def group_with_just_owner(third_group, root_user, users):
    third_group.members.create(
        {"user_id": users[0].id, "access_level": AccessLevel.OWNER.value}
    )
    third_group.members.delete(root_user.id)

    yield third_group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    third_group.members.create(
        {"user_id": root_user.id, "access_level": AccessLevel.OWNER.value}
    )

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        with allowed_codes(404):
            third_group.members.delete(user.id)


class TestMergeRequestApprovers:
    def test__only_users(self, project, make_user):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.username}
        """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 0
                found = True
        assert found

        user2 = make_user(AccessLevel.DEVELOPER)

        config_user_change = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.username}
        """

        run_gitlabform(config_user_change, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user2.username
                assert len(rule.groups) == 0
                found = True
        assert found

    def test__only_groups(
        self,
        project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
    ):
        config__approvers_single_group = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approver_groups:
                - {group_with_one_owner_and_two_developers.full_path}
        """

        run_gitlabform(config__approvers_single_group, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 0
                assert len(rule.groups) == 1
                assert (
                    rule.groups[0]["name"]
                    == group_with_one_owner_and_two_developers.name
                )
                found = True
        assert found

        config__approvers_single_group_change = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approver_groups:
                - {group_with_just_owner.full_path}
        """

        run_gitlabform(config__approvers_single_group_change, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 0
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == group_with_just_owner.name
                found = True
        assert found

    def test__single_user_and_single_group(
        self,
        project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config__approvers_single_user_and_single_group = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.username}
              approver_groups:
                - {group_with_one_owner_and_two_developers.full_path}
        """

        run_gitlabform(config__approvers_single_user_and_single_group, project)

        rules = project.approvalrules.list()
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 1
                assert (
                    rule.groups[0]["name"]
                    == group_with_one_owner_and_two_developers.name
                )
                found = True
        assert found

        user2 = make_user(AccessLevel.DEVELOPER)

        config__approvers_single_user_and_single_group_change = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.username}
              approver_groups:
                - {group_with_just_owner.full_path}
        """

        run_gitlabform(config__approvers_single_user_and_single_group_change, project)

        rules = project.approvalrules.list()
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user2.username
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == group_with_just_owner.name
                found = True
        assert found

    def test__more_than_one_user_and_more_than_one_group(
        self,
        project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)

        config__approvers_more_than_one_user_and_more_than_one_group = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.username}
                - {user2.username}
              approver_groups:
                - {group_with_one_owner_and_two_developers.full_path}
                - {group_with_just_owner.full_path}
        """

        run_gitlabform(
            config__approvers_more_than_one_user_and_more_than_one_group,
            project,
        )

        rules = project.approvalrules.list()
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == APPROVAL_RULE_NAME:
                assert len(rule.users) == 2
                usernames_in_rule = {user["username"] for user in rule.users}
                assert usernames_in_rule == {user1.username, user2.username}

                assert len(rule.groups) == 2
                groupnames_in_rule = {group["name"] for group in rule.groups}
                assert groupnames_in_rule == {
                    group_with_one_owner_and_two_developers.name,
                    group_with_just_owner.name,
                }
                found = True
        assert found

    def test__removing_preexisting_rules(
        self,
        project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)
        # add some preexisting approval rules
        project.approvalrules.create(
            {
                "name": "additional approval rule",
                "approvals_required": 1,
                "user_ids": [user1.id],
                "group_ids": [group_with_one_owner_and_two_developers.id],
            },
        )

        user2 = make_user(AccessLevel.DEVELOPER)
        config__approvers_removing_preexisting_approvals = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              remove_other_approval_rules: true
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.username}
              approver_groups:
                - {group_with_just_owner.full_path}
        """

        run_gitlabform(config__approvers_removing_preexisting_approvals, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.name == APPROVAL_RULE_NAME
        assert len(rule.users) == 1
        assert rule.users[0]["username"] == user2.username
        assert len(rule.groups) == 1
        assert rule.groups[0]["name"] == group_with_just_owner.name

    def test__inheritance(
        self,
        group,
        project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {group.full_path}/*:
            merge_requests:
              approvals:
                approvals_before_merge: 2
                reset_approvals_on_push: false
                disable_overriding_approvers_per_merge_request: true
                merge_requests_author_approval: false
              approvers:
                - {user1.username}
              approver_groups:
                - {group_with_just_owner.full_path}

          {project.path_with_namespace}:
            merge_requests:
              approvals:
                approvals_before_merge: 0
        """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.name == APPROVAL_RULE_NAME
        assert rule.approvals_required == 0
        assert len(rule.users) == 1
        assert rule.users[0]["username"] == user1.username
        assert len(rule.groups) == 1
        assert rule.groups[0]["name"] == group_with_just_owner.name
