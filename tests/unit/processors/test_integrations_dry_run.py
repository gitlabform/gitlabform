from unittest.mock import MagicMock, patch

from gitlabform.gitlab import GitLab
from gitlabform.processors.project.integrations_processor import IntegrationsProcessor


class _Processor(IntegrationsProcessor):
    def __init__(self, current_state):
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            super().__init__(MagicMock(GitLab))
        self._current_state = current_state

    def _get_current_state(self, project_and_group: str) -> dict:
        return self._current_state


def test_integrations_dry_run_shows_a_diff() -> None:
    current = {"pipelines-email": {"recipients": "old@example.com", "pipeline_events": True}}
    processor = _Processor(current)

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"pipelines-email": {"recipients": "new@example.com", "pipeline_events": True}},
            diff_only_changed=True,
        )

    logger.log_diff.assert_called_once_with(
        "integrations changes",
        current,
        {"pipelines-email": {"recipients": "new@example.com", "pipeline_events": True}},
        only_changed=True,
    )


def test_dry_run_drops_delete_only_entries_from_the_desired_state() -> None:
    processor = _Processor({})

    with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
        processor._print_diff(
            "group/project",
            {"slack": {"delete": True}, "webhook": {"webhook": "https://example.com"}},
            diff_only_changed=False,
        )

    assert logger.log_diff.call_args.args[2] == {"webhook": {"webhook": "https://example.com"}}


class _Integration:
    def __init__(self, name, settings):
        self.name = name
        self._settings = settings

    def asdict(self):
        return self._settings


def test_current_state_lists_configured_integrations() -> None:
    with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
        processor = IntegrationsProcessor(MagicMock(GitLab))
    project = MagicMock()
    project.integrations.list.return_value = [
        _Integration("pipelines-email", {"recipients": "a@example.com"}),
        _Integration("slack", {"webhook": "https://example.com"}),
    ]
    processor.gl.get_project_by_path_cached = MagicMock(return_value=project)

    assert processor._get_current_state("group/project") == {
        "pipelines-email": {"recipients": "a@example.com"},
        "slack": {"webhook": "https://example.com"},
    }
    project.integrations.list.assert_called_once_with(all=True)
