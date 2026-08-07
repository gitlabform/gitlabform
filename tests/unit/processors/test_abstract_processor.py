from unittest.mock import MagicMock, patch

from gitlabform.gitlab import GitLab
from gitlabform.processors import AbstractProcessor


class _TestableProcessor(AbstractProcessor):
    def _process_configuration(self, project_or_project_and_group: str, configuration: dict) -> None:
        pass


def _make_processor(name: str = "test_section") -> _TestableProcessor:
    with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
        return _TestableProcessor(name, MagicMock(GitLab))


class TestPrintDiff:
    def test_logs_not_supported_at_debug_when_getter_returns_none(self, caplog) -> None:
        # Base class implementation of _get_entities_for_diff returns None (opt out)
        processor = _make_processor("some_section")

        with caplog.at_level("DEBUG"):
            processor._print_diff("group/project", {"foo": 1}, diff_only_changed=False)

        matching = [r for r in caplog.records if "Diffing for section 'some_section'" in r.message]
        assert len(matching) == 1
        assert matching[0].levelname == "DEBUG"

    def test_calls_logger_with_entities_when_getter_overridden(self) -> None:
        class OverridingProcessor(_TestableProcessor):
            def _get_entities_for_diff(self, project_or_project_and_group, entity_config):
                return {"foo": "from-gitlab"}, entity_config

        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            processor = OverridingProcessor("test_section", MagicMock(GitLab))

        with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
            processor._print_diff("group/project", {"foo": "from-config"}, diff_only_changed=True)

        logger.log_diff.assert_called_once_with(
            "test_section changes",
            {"foo": "from-gitlab"},
            {"foo": "from-config"},
            only_changed=True,
        )

    def test_getter_receives_project_path_and_entity_config(self) -> None:
        received: dict = {}

        class OverridingProcessor(_TestableProcessor):
            def _get_entities_for_diff(self, project_or_project_and_group, entity_config):
                received["path"] = project_or_project_and_group
                received["config"] = entity_config
                return {}, {}

        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            processor = OverridingProcessor("t", MagicMock(GitLab))

        with patch("gitlabform.processors.abstract_processor.DifferenceLogger"):
            processor._print_diff("group/project", {"cfg": 1}, diff_only_changed=False)

        assert received == {"path": "group/project", "config": {"cfg": 1}}

    def test_getter_can_normalize_both_sides(self) -> None:
        class NormalizingProcessor(_TestableProcessor):
            def _get_entities_for_diff(self, project_or_project_and_group, entity_config):
                return (
                    {"foo": "gl:x"},
                    {k: f"cfg:{v}" for k, v in entity_config.items() if k != "meta"},
                )

        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            processor = NormalizingProcessor("t", MagicMock(GitLab))

        with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
            processor._print_diff("group/project", {"foo": "y", "meta": "drop"}, diff_only_changed=False)

        logger.log_diff.assert_called_once_with(
            "t changes",
            {"foo": "gl:x"},
            {"foo": "cfg:y"},
            only_changed=False,
        )


class TestRecursiveDiffAnalyzer:
    _cfg_a = [
        {
            "access_level": 40,
            "access_level_description": "Maintainers",
            "user_id": None,
            "group_id": None,
            "group_inheritance_type": 0,
        },
        {
            "access_level": 40,
            "access_level_description": "John Doe",
            "user_id": 967,
            "group_id": None,
            "group_inheritance_type": 0,
        },
    ]

    _cfg_b = [
        {"access_level": 40, "group_inheritance_type": 0},
        {"user_id": 967},
    ]

    def test__equal_configurations(self) -> None:
        assert not AbstractProcessor.recursive_diff_analyzer("deploy_access_levels", self._cfg_a, self._cfg_b)

    def test__unequal_configurations(self) -> None:
        modified_cfg = self._cfg_b.copy()

        modified_cfg[1]["group_inheritance_type"] = 1

        assert AbstractProcessor.recursive_diff_analyzer("deploy_access_levels", self._cfg_a, modified_cfg)
