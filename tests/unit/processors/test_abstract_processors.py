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

    abstract_proccessors.process_entity(
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

    abstract_proccessors.process_entity(
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
