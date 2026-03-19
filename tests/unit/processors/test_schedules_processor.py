"""
Transforming cron tests are defined in test_schedules_processor_extended_cron_pattern
"""

from unittest.mock import MagicMock

from gitlabform.processors.project import schedules_processor

processor = schedules_processor.SchedulesProcessor(gitlab=MagicMock())


def test_transform_config_when_chron_and_inputs_are_none():
    config = {"ref": "main", "cron_timezone": "Europe/Paris"}

    transformed_config = processor._transform_config(config, 1)

    assert transformed_config == config
    # Verify config has not been mutated
    assert config == {"ref": "main", "cron_timezone": "Europe/Paris"}


def test_transform_config_transforms_inputs_to_gitlab_rest_api_format():
    config = {
        "ref": "main",
        "cron_timezone": "Europe/Paris",
        "inputs": {"deploy_strategy": "blue-green", "feature_flags": ["flag1", "flag2"]},
    }

    transformed_config = processor._transform_config(config, 1)

    assert transformed_config == {
        "ref": "main",
        "cron_timezone": "Europe/Paris",
        "inputs": [
            {"name": "deploy_strategy", "value": "blue-green"},
            {"name": "feature_flags", "value": ["flag1", "flag2"]},
        ],
    }

    # Verify config has not been mutated
    assert config == {
        "ref": "main",
        "cron_timezone": "Europe/Paris",
        "inputs": {"deploy_strategy": "blue-green", "feature_flags": ["flag1", "flag2"]},
    }
