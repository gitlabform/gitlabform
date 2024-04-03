import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import allowed_codes, run_gitlabform

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
                assert (
                    rule.groups[0]["name"]
                    == group_with_one_owner_and_two_developers.name
                )
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
                assert (
                    rule.groups[0]["name"]
                    == group_with_one_owner_and_two_developers.full_path
                )
                protected_branches_name = [
                    branch["name"] for branch in rule.protected_branches
                ]
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
                assert (
                    rule.groups[0]["name"]
                    == group_with_one_owner_and_two_developers.full_path
                )
                protected_branches_name = sorted(
                    [branch["name"] for branch in rule.protected_branches]
                )
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

    def test__add_any_approver_rule_with_non_zero_approvals_required(
        self, project, make_user
    ):
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

    @pytest.mark.skip(
        reason="Group level merge_request_approval_rules are Experimental: https://docs.gitlab.com/ee/api/merge_request_approvals.html#group-level-mr-approvals."
    )
    def test__group_config_with_code_coverage_merge_request_approval_rule(
        self, gl, project, users
    ):
        parent_groups = project.groups.list()
        group_id = parent_groups[0].id

        parent_group = gl.groups.get(group_id)

        config = f"""
        projects_and_groups:
          {parent_group.full_path}/*::
            merge_requests_approval_rules:
              enforce: true
              code_coverage:
                applies_to_all_protected_branches: true
                approvals_required: 1
                name: "Coverage-Check"
                users:
                  - {users[0].username}
                report_type: code_coverage
                rule_type: report_approver
        """

        run_gitlabform(config, parent_group)

        rules = project.approvalrules.list()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.approvals_required == 1
        assert rule.name == "Coverage-Check"
        assert rule.report_type == "code_coverage"
        assert rule.rule_type == "report_approver"

    @pytest.mark.skip(
        reason="Group level merge_request_approval_rules are Experimental: https://docs.gitlab.com/ee/api/merge_request_approvals.html#group-level-mr-approvals."
    )
    def test__project_overriding_group_level_merge_request_approval_rule(
        self, gl, project, users
    ):
        parent_groups = project.groups.list()
        group_id = parent_groups[0].id

        parent_group = gl.groups.get(group_id)

        other_project_id = gl.projects.create(
            {"name": "Override-Project", "namespace_id": group_id}
        ).id
        other_project = project.projects.get(other_project_id)

        config = f"""
        projects_and_groups:
          {parent_group.full_path}/*::
            merge_requests_approval_rules:
              enforce: true
              any:
                approvals_required: 1
                rule_type: any_approver
                name: "Any approver"
              code_coverage:
                applies_to_all_protected_branches: true
                approvals_required: 1
                name: "Coverage-Check"
                users:
                  - {users[0].username}
                report_type: code_coverage
                rule_type: report_approver
          {other_project.path_with_namespace}:
            merge_requests_approval_rules:
              any:
                approvals_required: 0
                rule_type: any_approver
                name: "Any approver"
              enforce: true
        """

        run_gitlabform(config, parent_group)

        project_rules = project.approvalrules.list()

        assert len(project_rules) == 2
        any_rule = project_rules[0]
        assert any_rule.approvals_required == 1
        assert any_rule.name == "All project members"
        assert any_rule.rule_type == "any_approver"
        coverage_rule = project_rules[1]
        assert coverage_rule.approvals_required == 1
        assert coverage_rule.name == "Coverage-Check"
        assert coverage_rule.rule_type == "report_approver"

        other_project_rules = other_project.approvalrules.list()

        assert len(other_project_rules) == 1
        any_rule = other_project_rules[0]
        assert any_rule.approvals_required == 1
        assert any_rule.name == "All project members"
        assert any_rule.rule_type == "any_approver"

    def test__add_rules__common_and_subgroup(
        self,
        project,
        subgroup,
        project_in_subgroup,
        other_group,
        third_group,
        make_user,
        branch,
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
                  {branch}:
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
                      - {branch}
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
                assert rule.protected_branches[0]["name"] == branch
                second_found = True

        assert first_found and second_found
