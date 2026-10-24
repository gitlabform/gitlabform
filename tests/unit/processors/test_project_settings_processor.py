from unittest.mock import MagicMock, patch

from gitlabform.gitlab import GitLab
from gitlabform.processors.project.project_settings_processor import ProjectSettingsProcessor


class _Processor(ProjectSettingsProcessor):
    def __init__(self, current_state: dict):
        super().__init__(MagicMock(GitLab), strict=False)
        self._current_state = current_state

    def _get_current_state(self, project_path: str) -> dict:
        return self._current_state


def _make_processor(current_state: dict) -> _Processor:
    with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
        return _Processor(current_state)


def test_dry_run_resolves_keep_existing_topics() -> None:
    processor = _make_processor({"topics": ["foo", "bar"]})

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"topics": [{"keep_existing": True}, "new-topic"]},
            diff_only_changed=True,
        )

    logger.log_diff.assert_called_once_with(
        "project_settings changes",
        {"topics": ["foo", "bar"]},
        {"topics": ["foo", "bar", "new-topic"]},
        only_changed=True,
    )


def test_dry_run_resolves_delete_topic_markers() -> None:
    processor = _make_processor({"topics": ["foo", "bar"]})

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"topics": [{"foo": {"delete": True}}, "baz"]},
            diff_only_changed=False,
        )

    logger.log_diff.assert_called_once_with(
        "project_settings changes",
        {"topics": ["foo", "bar"]},
        {"topics": ["baz"]},
        only_changed=False,
    )


def test_dry_run_does_not_mutate_the_configuration() -> None:
    processor = _make_processor({"topics": ["foo"]})
    configuration = {"topics": [{"keep_existing": True}, "new-topic"]}

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger"):
        processor._print_diff("group/project", configuration, diff_only_changed=False)

    assert configuration == {"topics": [{"keep_existing": True}, "new-topic"]}
