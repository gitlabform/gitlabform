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


class TestMergeRequestApprovers:
    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__add_single_rule(self, gitlab, group_and_project, make_user):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {group_and_project}:
            merge_requests_approval_rules:
              standard:
                approvals_required: 1
                name: "Regular approvers"
                users:
                  - {user1.name}
        """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule["name"] == "Regular approvers":
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 0
                found = True
        assert found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__add_two_rules(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    # protected_branches:
                    #   - sensitive-branch 
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) >= 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule["name"] == "Regular approvers":
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 0
                first_found = True
            if rule["name"] == "Extra Security Team approval for selected branches":
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 1
                assert (
                    rule["groups"][0]["name"] == group_with_one_owner_and_two_developers
                )
                second_found = True

        assert first_found and second_found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__enforce(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    # protected_branches:
                    #   - sensitive-branch 
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) >= 2

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.name}
                  enforce: true
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) == 1

        rule = rules[0]
        assert rule["name"] == "Regular approvers"
        assert len(rule["users"]) == 1
        assert rule["users"][0]["username"] == user1.name
        assert len(rule["groups"]) == 0

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__edit_rules(
        self,
        gitlab,
        group_and_project,
        group_with_one_owner_and_two_developers,
        make_user,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    # protected_branches:
                    #   - sensitive-branch 
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) >= 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule["name"] == "Regular approvers":
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 0
                first_found = True
            if rule["name"] == "Extra Security Team approval for selected branches":
                assert rule["approvals_required"] == 2
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 1
                assert (
                    rule["groups"][0]["name"] == group_with_one_owner_and_two_developers
                )
                # assert rule["protected_branches"] == ["sensitive-branch"]
                second_found = True

        assert first_found and second_found

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  # this is needed for renaming rules
                  enforce: true
                  standard:
                    approvals_required: 1
                    name: "Regular approvers but new" # changed
                    users:
                      - {user1.name}
                  security:
                    approvals_required: 1 # changed
                    name: "Extra Security Team approval for selected branches"
                    # changed
                    # users:
                    #   - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    # protected_branches:
                    #   - sensitive-branch 
                    #   - another # changed
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) == 2  # because of enforce

        first_found = False
        second_found = False
        for rule in rules:
            # this rule should have been deleted
            assert not rule["name"] == "Regular approvers"

            if rule["name"] == "Regular approvers but new":  # changed
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["groups"]) == 0
                first_found = True
            if rule["name"] == "Extra Security Team approval for selected branches":
                assert rule["approvals_required"] == 1  # changed
                assert len(rule["users"]) == 0  # changed
                assert len(rule["groups"]) == 1
                assert (
                    rule["groups"][0]["name"] == group_with_one_owner_and_two_developers
                )
                # assert rule["protected_branches"] == [
                #     "sensitive-branch",
                #     "another",
                # ]  # changed
                second_found = True

        assert first_found and second_found

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__add_any_approver_rule(self, gitlab, group_and_project, make_user):

        config = f"""
            projects_and_groups:
              {group_and_project}:
                merge_requests_approval_rules:
                  any:
                    approvals_required: 0
                    rule_type: any_approver
                    name: "Any approver"
                  enforce: true
            """

        run_gitlabform(config, group_and_project)

        rules = gitlab.get_approval_rules(group_and_project)

        assert len(rules) == 1
        rule = rules[0]
        assert rule["approvals_required"] == 0
        assert rule["name"] == "Any approver"
        assert rule["rule_type"] == "any_approver"
