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
    def test_logs_not_supported_at_debug_when_no_getter_configured(self, caplog) -> None:
        processor = _make_processor("some_section")

        with caplog.at_level("DEBUG"):
            processor._print_diff("group/project", {"foo": 1}, diff_only_changed=False)

        matching = [r for r in caplog.records if "Diffing for section 'some_section'" in r.message]
        assert len(matching) == 1
        assert matching[0].levelname == "DEBUG"

    def test_calls_logger_with_entities_when_getter_set(self) -> None:
        processor = _make_processor("test_section")
        processor.get_entity_in_gitlab = MagicMock(return_value={"foo": "from-gitlab"})
        entity_config = {"foo": "from-config"}

        with patch("gitlabform.processors.abstract_processor.DifferenceLogger") as logger:
            processor._print_diff("group/project", entity_config, diff_only_changed=True)

        processor.get_entity_in_gitlab.assert_called_once_with("group/project")
        logger.log_diff.assert_called_once_with(
            "test_section changes",
            {"foo": "from-gitlab"},
            {"foo": "from-config"},
            only_changed=True,
        )

    def test_prepare_entities_default_is_identity(self) -> None:
        processor = _make_processor()
        gitlab_side = {"a": 1}
        config_side = {"b": 2}

        result = processor._prepare_entities_for_diff(gitlab_side, config_side)

        assert result == (gitlab_side, config_side)

    def test_prepare_entities_override_transforms_both_sides(self) -> None:
        class TransformingProcessor(_TestableProcessor):
            def _prepare_entities_for_diff(self, entity_in_gitlab, entity_config):
                return (
                    {k: f"gl:{v}" for k, v in entity_in_gitlab.items()},
                    {k: f"cfg:{v}" for k, v in entity_config.items() if k != "meta"},
                )

        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            processor = TransformingProcessor("t", MagicMock(GitLab))
        processor.get_entity_in_gitlab = MagicMock(return_value={"foo": "x"})

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
