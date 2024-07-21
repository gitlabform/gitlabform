from gitlabform.processors.util.branch_protector import BranchProtector


def test_get_current_permissions_handles_zero_access_level():
    test_protected_branches_response = {
        "id": 1,
        "name": "master",
        "push_access_levels": [
            {"access_level": 0, "access_level_description": "Push Description"}
        ],
        "merge_access_levels": [
            {"access_level": 40, "access_level_description": "Merge Description"}
        ],
        "allow_force_push": False,
        "code_owner_approval_required": False,
    }

    push_levels, _, _ = BranchProtector.get_current_permissions(
        test_protected_branches_response, "push"
    )
    assert push_levels == [0]

    merge_levels, _, _ = BranchProtector.get_current_permissions(
        test_protected_branches_response, "merge"
    )
    assert merge_levels == [40]
