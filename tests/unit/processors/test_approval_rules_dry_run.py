from unittest.mock import MagicMock, patch

from gitlabform.gitlab import GitLab
from gitlabform.processors.project.merge_requests_approval_rules import (
    MergeRequestsApprovalRules,
)


def _make_processor(rules: list[dict]) -> MergeRequestsApprovalRules:
    with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
        processor = MergeRequestsApprovalRules(MagicMock(GitLab))
    processor.list_method = MagicMock(return_value=rules)
    return processor


def test_dry_run_diff_pairs_rules_by_name() -> None:
    rules = [
        {"id": 1, "name": "All Members", "approvals_required": 2},
        {"id": 2, "name": "Security", "approvals_required": 1},
    ]
    processor = _make_processor(rules)

    config = {"any": {"name": "All Members", "approvals_required": 1}, "enforce": True}
    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff("group/project", config, diff_only_changed=True)

    logger.log_diff.assert_called_once_with(
        "merge_requests_approval_rules changes",
        {"All Members": rules[0], "Security": rules[1]},
        {"All Members": {"name": "All Members", "approvals_required": 1}},
        only_changed=True,
    )


def test_dry_run_diff_drops_enforce_from_the_desired_state() -> None:
    processor = _make_processor([])

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"any": {"name": "All Members", "approvals_required": 1}, "enforce": False},
            diff_only_changed=False,
        )

    desired = logger.log_diff.call_args.args[2]
    assert "enforce" not in desired
