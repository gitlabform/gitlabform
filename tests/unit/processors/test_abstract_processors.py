from unittest.mock import MagicMock
from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.output import EffectiveConfigurationFile
from gitlabform.processors import AbstractProcessors
from gitlabform.processors.abstract_processor import AbstractProcessor


def test_can_exclude_sections() -> None:
    mock_gitlab = MagicMock(GitLab)
    test_config: Configuration = MagicMock(Configuration)

    abstract_proccessors = AbstractProcessors(gitlab=mock_gitlab, config=test_config, strict=False)

    group_members_processor = MagicMock(AbstractProcessor)
    group_members_processor.configuration_name = "group_members"

    project_members_processor = MagicMock(AbstractProcessor)
    project_members_processor.configuration_name = "project_members"

    abstract_proccessors.processors = [group_members_processor, project_members_processor]

    exclude_sections = ["group_members"]

    only_sections = "all"

    processed = abstract_proccessors.process_entity(
        entity_reference="test-group/project",
        configuration=MagicMock(dict),
        dry_run=False,
        diff_only_changed=False,
        effective_configuration=MagicMock(EffectiveConfigurationFile),
        only_sections=only_sections,
        exclude_sections=exclude_sections,
    )

    project_members_processor.process.assert_called_once()
    group_members_processor.process.assert_not_called()
    assert processed == 1


def test_can_process_only_sections() -> None:
    mock_gitlab = MagicMock(GitLab)
    test_config: Configuration = MagicMock(Configuration)

    abstract_proccessors = AbstractProcessors(gitlab=mock_gitlab, config=test_config, strict=False)

    group_members_processor = MagicMock(AbstractProcessor)
    group_members_processor.configuration_name = "group_members"

    project_members_processor = MagicMock(AbstractProcessor)
    project_members_processor.configuration_name = "project_members"

    abstract_proccessors.processors = [group_members_processor, project_members_processor]

    only_sections = ["group_members"]
    exclude_sections: list[str] = []

    processed = abstract_proccessors.process_entity(
        entity_reference="test-group/project",
        configuration=MagicMock(dict),
        dry_run=False,
        diff_only_changed=False,
        effective_configuration=MagicMock(EffectiveConfigurationFile),
        only_sections=only_sections,
        exclude_sections=exclude_sections,
    )

    project_members_processor.process.assert_not_called()
    group_members_processor.process.assert_called_once()
    assert processed == 1


def test_process_entity_returns_zero_when_all_sections_excluded() -> None:
    abstract_proccessors = AbstractProcessors(gitlab=MagicMock(GitLab), config=MagicMock(Configuration), strict=False)

    settings_processor = MagicMock(AbstractProcessor)
    settings_processor.configuration_name = "settings"
    abstract_proccessors.processors = [settings_processor]

    processed = abstract_proccessors.process_entity(
        entity_reference="",
        configuration=MagicMock(dict),
        dry_run=False,
        diff_only_changed=False,
        effective_configuration=MagicMock(EffectiveConfigurationFile),
        only_sections="all",
        exclude_sections=["settings"],
    )

    settings_processor.process.assert_not_called()
    assert processed == 0
