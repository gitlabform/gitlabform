import pytest
from ez_yaml import ez_yaml

from configuration.transform import UserTransformer
from gitlabform import Configuration
from tests.acceptance import run_gitlabform, gl
from gitlabform.gitlab import AccessLevel


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
        branch,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
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
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    protected_branches:
                      - {branch} 
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
                assert len(rule["protected_branches"]) == 1
                assert rule["protected_branches"][0]["name"] == branch
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
        branch,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
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
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    protected_branches:
                      - {branch} 
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
        branch,
        other_branch,
    ):

        user1 = make_user(AccessLevel.DEVELOPER)

        config = f"""
            projects_and_groups:
              {group_and_project}:
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
                      - {user1.name}
                  security:
                    approvals_required: 2
                    name: "Extra Security Team approval for selected branches"
                    users:
                      - {user1.name}
                    groups:
                      - {group_with_one_owner_and_two_developers}
                    protected_branches:
                      - {branch} 
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
                protected_branches_name = [
                    branch["name"] for branch in rule["protected_branches"]
                ]
                assert protected_branches_name == [branch]
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
                    protected_branches:
                      - {branch} 
                      - {other_branch} # changed
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
                protected_branches_name = sorted(
                    [branch["name"] for branch in rule["protected_branches"]]
                )
                assert protected_branches_name == sorted(
                    [
                        branch,
                        other_branch,
                    ]
                )  # changed
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

    @pytest.mark.skipif(
        gl.has_no_license(), reason="this test requires a GitLab license (Paid/Trial)"
    )
    def test__add_rules__common_and_subgroup(
        self,
        gitlab,
        group_and_project,
        sub_group,
        project_in_sub_group,
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
 
              "{sub_group}/*":
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
                      - {other_group}
                    users:
                      - {user1.name}
                    protected_branches:
                      - {branch}
                  enforce: true
            """

        config_object = Configuration(config_string=config)
        ut = UserTransformer(gitlab)
        ut.transform(config_object, last=True)

        effective_config_yaml_str = ez_yaml.to_string(
            obj=config_object.config, options={}
        )
        print("!!!Transformed:")
        print(effective_config_yaml_str)

        effective_config = config_object.get_effective_config_for_group(
            project_in_sub_group
        )
        effective_config_yaml_str = ez_yaml.to_string(obj=effective_config, options={})
        print("!!!Effective:")
        print(effective_config_yaml_str)

        run_gitlabform(config, "ALL_DEFINED")

        rules = gitlab.get_approval_rules(project_in_sub_group)

        assert len(rules) == 2

        first_found = False
        second_found = False
        for rule in rules:
            if rule["name"] == "All eligible users":
                assert len(rule["groups"]) == 0
                first_found = True
            if rule["name"] == "Dev Code Review - UAT":
                assert len(rule["groups"]) == 1
                assert rule["groups"][0]["name"] == other_group
                assert len(rule["users"]) == 1
                assert rule["users"][0]["username"] == user1.name
                assert len(rule["protected_branches"]) == 1
                assert rule["protected_branches"][0]["name"] == branch
                second_found = True

        assert first_found and second_found
