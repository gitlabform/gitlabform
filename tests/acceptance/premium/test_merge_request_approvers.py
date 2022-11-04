import pytest

from tests.acceptance import run_gitlabform, gl
from gitlabform.gitlab import AccessLevel
from gitlabform.processors.project.merge_requests_processor import APPROVAL_RULE_NAME


@pytest.fixture(scope="function")
def group_with_one_owner_and_two_developers(gitlab, other_group, users):

    gitlab.add_member_to_group(other_group, users[0], AccessLevel.OWNER.value)
    gitlab.add_member_to_group(other_group, users[1], AccessLevel.DEVELOPER.value)
    gitlab.add_member_to_group(other_group, users[2], AccessLevel.DEVELOPER.value)
    gitlab.remove_member_from_group(other_group, "root")

    yield other_group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    gitlab.add_member_to_group(other_group, "root", AccessLevel.OWNER.value)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_group(other_group, user)


@pytest.fixture(scope="function")
def group_with_just_owner(gitlab, third_group, users):

    gitlab.add_member_to_group(third_group, users[0], AccessLevel.OWNER.value)
    gitlab.remove_member_from_group(third_group, "root")

    yield third_group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    gitlab.add_member_to_group(third_group, "root", AccessLevel.OWNER.value)

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        gitlab.remove_member_from_group(third_group, user)


class TestMergeRequestApprovers:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__only_users(self, gitlab, group_and_project, make_user):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.name}
        """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approvals_rules(group_and_project)

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 0
                found = True
        assert found

        user2 = make_user(AccessLevel.DEVELOPER)

        config_user_change = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.name}
        """

        run_gitlabform(config_user_change, group_and_project)

        rules = gitlab.get_approvals_rules(group_and_project)

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user2.name
                assert len(rule["groups"]) == 0
                found = True
        assert found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__only_groups(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
    ):
        config__approvers_single_group = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approver_groups:
                - {group_with_one_owner_and_two_developers}
        """

        run_gitlabform(config__approvers_single_group, group_and_project)

        rules = gitlab.get_approvals_rules(group_and_project)

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 0
                assert len(rule["groups"]) == 1
                assert (
                    rule["groups"][0]["name"] == group_with_one_owner_and_two_developers
                )
                found = True
        assert found

        config__approvers_single_group_change = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approver_groups:
                - {group_with_just_owner}
        """

        run_gitlabform(config__approvers_single_group_change, group_and_project)

        rules = gitlab.get_approvals_rules(group_and_project)

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 0
                assert len(rule["groups"]) == 1
                assert rule["groups"][0]["name"] == group_with_just_owner
                found = True
        assert found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__single_user_and_single_group(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config__approvers_single_user_and_single_group = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.name}
              approver_groups:
                - {group_with_one_owner_and_two_developers}
        """

        run_gitlabform(
            config__approvers_single_user_and_single_group, group_and_project
        )

        rules = gitlab.get_approvals_rules(group_and_project)
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 1
                assert (
                    rule["groups"][0]["name"] == group_with_one_owner_and_two_developers
                )
                found = True
        assert found

        user2 = make_user(AccessLevel.DEVELOPER)

        config__approvers_single_user_and_single_group_change = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.name}
              approver_groups:
                - {group_with_just_owner}
        """

        run_gitlabform(
            config__approvers_single_user_and_single_group_change, group_and_project
        )

        rules = gitlab.get_approvals_rules(group_and_project)
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user2.name
                assert len(rule["groups"]) == 1
                assert rule["groups"][0]["name"] == group_with_just_owner
                found = True
        assert found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__more_than_one_user_and_more_than_one_group(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)
        user2 = make_user(AccessLevel.DEVELOPER)

        config__approvers_more_than_one_user_and_more_than_one_group = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user1.name}
                - {user2.name}
              approver_groups:
                - {group_with_one_owner_and_two_developers}
                - {group_with_just_owner}
        """

        run_gitlabform(
            config__approvers_more_than_one_user_and_more_than_one_group,
            group_and_project,
        )

        rules = gitlab.get_approvals_rules(group_and_project)
        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == APPROVAL_RULE_NAME:
                assert len(rule["users"]) == 2
                usernames_in_rule = {user["username"] for user in rule["users"]}
                assert usernames_in_rule == {user1.name, user2.name}

                assert len(rule["groups"]) == 2
                groupnames_in_rule = {group["name"] for group in rule["groups"]}
                assert groupnames_in_rule == {
                    group_with_one_owner_and_two_developers,
                    group_with_just_owner,
                }
                found = True
        assert found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__removing_preexisting_rules(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        group_with_just_owner,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)
        # add some preexisting approval rules
        gitlab.create_approval_rule(
            group_and_project,
            "additional approval rule",
            1,
            [user1.name],
            [group_with_one_owner_and_two_developers],
        )

        user2 = make_user(AccessLevel.DEVELOPER)
        config__approvers_removing_preexisting_approvals = f"""
        projects_and_groups:
          {group_and_project}:
            project_settings:
              merge_requests_access_level: "enabled"
            merge_requests:
              remove_other_approval_rules: true
              approvals:
                approvals_before_merge: 1
                reset_approvals_on_push: true
                disable_overriding_approvers_per_merge_request: true
              approvers:
                - {user2.name}
              approver_groups:
                - {group_with_just_owner}
        """

        run_gitlabform(
            config__approvers_removing_preexisting_approvals, group_and_project
        )

        rules = gitlab.get_approvals_rules(group_and_project)

        assert len(rules) == 1
        rule = rules[0]
        assert rule["name"] == APPROVAL_RULE_NAME
        assert len(rule["users"]) == 1
        assert rule["users"][0]["username"] == user2.name
        assert len(rule["groups"]) == 1
        assert rule["groups"][0]["name"] == group_with_just_owner
