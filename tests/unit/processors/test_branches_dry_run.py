from unittest.mock import MagicMock, patch

from gitlabform.gitlab import GitLab
from gitlabform.processors.project.branches_processor import BranchesProcessor


class _Protected:
    def __init__(self, name, data):
        self.name = name
        self._data = data

    def asdict(self):
        return self._data


def _processor() -> BranchesProcessor:
    with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
        return BranchesProcessor(MagicMock(GitLab), strict=False)


def test_current_state_lists_protected_branches() -> None:
    processor = _processor()
    project = MagicMock()
    project.protectedbranches.list.return_value = [
        _Protected("main", {"name": "main", "allow_force_push": False}),
        _Protected("release/*", {"name": "release/*", "allow_force_push": True}),
    ]
    processor.gl.get_project_by_path_cached = MagicMock(return_value=project)

    assert processor._get_current_state("group/project") == {
        "main": {"name": "main", "allow_force_push": False},
        "release/*": {"name": "release/*", "allow_force_push": True},
    }
    project.protectedbranches.list.assert_called_once_with(all=True)


def test_desired_state_skips_the_processor_directive() -> None:
    processor = _processor()

    desired = processor._get_desired_state(
        {
            "skip_missing_branch": True,
            "main": {"protected": True, "allow_force_push": False},
        }
    )

    assert "skip_missing_branch" not in desired
    assert desired["main"]["allow_force_push"] is False


def test_branches_dry_run_logs_a_diff() -> None:
    processor = _processor()
    current = {"main": {"name": "main", "allow_force_push": True}}
    processor._get_current_state = MagicMock(return_value=current)

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"main": {"protected": True, "allow_force_push": False}},
            diff_only_changed=True,
        )

    logger.log_diff.assert_called_once()
    assert logger.log_diff.call_args.args[0] == "branches changes"
    assert logger.log_diff.call_args.args[1] == current
