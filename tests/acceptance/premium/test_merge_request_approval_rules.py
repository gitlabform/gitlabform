import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import allowed_codes, run_gitlabform

pytestmark = pytest.mark.requires_license


@pytest.fixture(scope="function")
def group_with_one_owner_and_two_developers(other_group, root_user, users):
    other_group.members.create({"user_id": users[0].id, "access_level": AccessLevel.OWNER.value})
    other_group.members.create({"user_id": users[1].id, "access_level": AccessLevel.DEVELOPER.value})
    other_group.members.create({"user_id": users[2].id, "access_level": AccessLevel.DEVELOPER.value})
    other_group.members.delete(root_user.id)

    yield other_group

    # we are running tests with root's token, so every group is created
    # with a single user - root as owner. we restore the group to
    # this state here.

    other_group.members.create({"user_id": root_user.id, "access_level": AccessLevel.OWNER.value})

    # we try to remove all users, not just those added above,
    # on purpose, as more may have been added in the tests
    for user in users:
        with allowed_codes(404):
            other_group.members.delete(user.id)


class TestMergeRequestApprovers:
    def test__add_single_rule(self, project, make_user):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            merge_requests_approval_rules:
              standard:
                approvals_required: 1
                name: "Regular approvers"
                users:
                  - {user1.username}
        """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 1

        found = False
        for rule in rules:
            if rule.name == "Regular approvers":
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 0
                found = True
        assert found

    def test__add_two_rules(
        self,
        project,
        group_with_one_owner_and_two_developers,
        make_user,
        branch,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  {branch}:
                    protected: true
                    push_access_level: no access
                    merge_access_level: developer
                    unprotect_access_level: maintainer
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.username}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.username}
                    groups:
                      - {group_with_one_owner_and_two_developers.full_path}
                    protected_branches:
                      - {branch} 
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule.name == "Regular approvers":
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 0
                first_found = True
            if rule.name == "Extra Security Team approval for selected branches":
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == group_with_one_owner_and_two_developers.name
                assert len(rule.protected_branches) == 1
                assert rule.protected_branches[0]["name"] == branch
                second_found = True

        assert first_found and second_found

    def test__enforce(
        self,
        project,
        group_with_one_owner_and_two_developers,
        make_user,
        branch,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  {branch}:
                    protected: true
                    push_access_level: no access
                    merge_access_level: developer
                    unprotect_access_level: maintainer
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.username}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.username}
                    groups:
                      - {group_with_one_owner_and_two_developers.full_path}
                    protected_branches:
                      - {branch} 
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 2

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.username}
                  enforce: true
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1

        rule = rules[0]
        assert rule.name == "Regular approvers"
        assert len(rule.users) == 1
        assert rule.users[0]["username"] == user1.username
        assert len(rule.groups) == 0

    def test__edit_rules(
        self,
        project,
        group_with_one_owner_and_two_developers,
        make_user,
        branch,
        other_branch,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                branches:
                  {branch}:
                    protected: true
                    push_access_level: no access
                    merge_access_level: developer
                    unprotect_access_level: maintainer
                  {other_branch}:
                    protected: true
                    push_access_level: no access
                    merge_access_level: developer
                    unprotect_access_level: maintainer
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "Regular approvers"
                    users:
                      - {user1.username}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.username}
                    groups:
                      - {group_with_one_owner_and_two_developers.full_path}
                    protected_branches:
                      - {branch} 
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) >= 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule.name == "Regular approvers":
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 0
                first_found = True
            if rule.name == "Extra Security Team approval for selected branches":
                assert rule.approvals_required == 2
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == group_with_one_owner_and_two_developers.full_path
                protected_branches_name = [branch["name"] for branch in rule.protected_branches]
                assert protected_branches_name == [branch]
                second_found = True

        assert first_found and second_found

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                merge_requests_approval_rules:
                  # this is needed for renaming rules
                  enforce: true
                  standard:
                    approvals_required: 1
                    name: "Regular approvers but new" # changed
                    users:
                      - {user1.username}
                  security:
                    approvals_required: 1 # changed
                    name: "Extra Security Team approval for selected branches"
                    # changed
                    # users:
                    #   - {user1.username}
                    groups:
                      - {group_with_one_owner_and_two_developers.full_path}
                    protected_branches:
                      - {branch} 
                      - {other_branch} # changed
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 2  # because of enforce

        first_found = False
        second_found = False
        for rule in rules:
            # this rule should have been deleted
            assert not rule.name == "Regular approvers"

            if rule.name == "Regular approvers but new":  # changed
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.groups) == 0
                first_found = True
            if rule.name == "Extra Security Team approval for selected branches":
                assert rule.approvals_required == 1  # changed
                assert len(rule.users) == 0  # changed
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == group_with_one_owner_and_two_developers.full_path
                protected_branches_name = sorted([branch["name"] for branch in rule.protected_branches])
                assert protected_branches_name == sorted(
                    [
                        branch,
                        other_branch,
                    ]
                )  # changed
                second_found = True

        assert first_found and second_found

    def test__add_any_approver_rule(self, project, make_user):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                merge_requests_approval_rules:
                  any:
                    approvals_required: 0
                    rule_type: any_approver
                    name: "Any approver"
                  enforce: true
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.approvals_required == 0
        assert rule.name == "Any approver"
        assert rule.rule_type == "any_approver"

    def test__add_any_approver_rule_with_non_zero_approvals_required(self, project, make_user):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                merge_requests_approval_rules:
                  any:
                    approvals_required: 2
                    rule_type: any_approver
                    name: "Any approver"
                  enforce: true
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.approvals_required == 2
        assert rule.name == "Any approver"
        assert rule.rule_type == "any_approver"

    def test__add_any_approver_rule_with_non_default_name(self, project, make_user):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                merge_requests_approval_rules:
                  any:
                    approvals_required: 0
                    rule_type: any_approver
                    name: "All project members"
                  enforce: true
            """

        run_gitlabform(config, project)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.approvals_required == 0
        assert rule.name == "All project members"
        assert rule.rule_type == "any_approver"

    def test__add_rules__common_and_subgroup(
        self,
        project,
        subgroup,
        project_in_subgroup,
        other_group,
        third_group,
        make_user,
    ):
        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              "*":
                merge_requests_approval_rules:
                  standard:
                    approvals_required: 1
                    name: "All eligible users"
                  enforce: true
 
              "{subgroup.full_path}/*":

                members:
                  users:
                    {user1.username}:
                      access_level: {AccessLevel.DEVELOPER.value}

                branches:
                  main:
                    protected: true
                    push_access_level: no access
                    merge_access_level: developer
                    unprotect_access_level: maintainer

                merge_requests_approval_rules:
                  dev-uat:
                    approvals_required: 1
                    name: "Dev Code Review - UAT"
                    groups:
                      - {other_group.full_path}
                    users:
                      - {user1.username}
                    protected_branches:
                      - main
                  enforce: true
            """

        run_gitlabform(config, project_in_subgroup)

        rules = project_in_subgroup.approvalrules.list()

        assert len(rules) == 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule.name == "All eligible users":
                assert len(rule.groups) == 0
                first_found = True
            if rule.name == "Dev Code Review - UAT":
                assert len(rule.groups) == 1
                assert rule.groups[0]["name"] == other_group.name
                assert len(rule.users) == 1
                assert rule.users[0]["username"] == user1.username
                assert len(rule.protected_branches) == 1
                assert rule.protected_branches[0]["name"] == "main"
                second_found = True

        assert first_found and second_found

    def test__merge_request_approval_rule_dependent_on_members(
        self, project_for_function, group_for_function, make_user
    ):
        """
        Configure merge request approval rule setting that depends on users or groups,
        Make sure the setting is applied successfully because users must be members
        before they can be configured in approval rule setting.
        """

        user_for_group_to_share_project_with = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)
        project_user_for_approval_rule = make_user(level=AccessLevel.DEVELOPER, add_to_project=False)

        config_branch_protection = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_members:
              users:
                {user_for_group_to_share_project_with.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
          {project_for_function.path_with_namespace}:
            members:
              users:
                {project_user_for_approval_rule.username}:
                  access_level: {AccessLevel.DEVELOPER.value}
              groups:
                {group_for_function.full_path}:
                  group_access: {AccessLevel.DEVELOPER.value}
            merge_requests_approval_rules:
              default:
                name: "Special approvers"
                approvals_required: 2
                users:
                  - {project_user_for_approval_rule.username}
                groups:
                  - {group_for_function.full_path}
        """

        run_gitlabform(config_branch_protection, project_for_function)

        mr_approval_rules_under_this_project = project_for_function.approvalrules.list()
        assert len(mr_approval_rules_under_this_project) == 1
        default_mr_approval_rule_details = mr_approval_rules_under_this_project[0]
        assert default_mr_approval_rule_details.name == "Special approvers"
        print("approval rule details:", default_mr_approval_rule_details)

        assert default_mr_approval_rule_details.approvals_required == 2
        assert len(default_mr_approval_rule_details.users) == 1
        assert default_mr_approval_rule_details.users[0]["username"] == project_user_for_approval_rule.username
        assert len(default_mr_approval_rule_details.groups) == 1
        assert default_mr_approval_rule_details.groups[0]["path"] == group_for_function.full_path
