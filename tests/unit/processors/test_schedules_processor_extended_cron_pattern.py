import pytest

from gitlabform.processors.project import schedules_processor


@pytest.mark.parametrize(
    ("project_id", "cron", "expected"),
    [
        (1, "* * * * *", "* * * * *"),
        (1, "@HOURLY", "8 * * * *"),
        (1, "H * * * *", "8 * * * *"),
        (1, "@daily", "8 18 * * *"),
        (1, "H H * * *", "8 18 * * *"),
        (1, "@weekly", "8 18 * * 6"),
        (1, "H H * * H", "8 18 * * 6"),
        (1, "@nightly", "8 4 * * *"),
        (2, "H * * * *", "55 * * * *"),
        (2, "H H * * *", "55 1 * * *"),
        (3, "H * * * *", "15 * * * *"),
        (3, "H H * * *", "15 18 * * *"),
        (3, "H(10-14) H * * *", "11 18 * * *"),
        (3, "H(15-20),H(45-50)  H(1-7) * *       *", "16,49 5 * * *"),
        (3, "H(15-20),H(45-50)  H(01-07) * * MON-FRI", "16,49 5 * * MON-FRI"),
        (4, "H H * * *", "15 9 * * *"),
        (5, "*/10 01-07,20-23 * * *", "*/10 01-07,20-23 * * *"),
        (5, "H/15 */4 * * *", "8,23,38,53 */4 * * *"),
        (5, "H/20 H/4,H * * *", "19,39,59 2,6,10,14,18,22,23 * * *"),
    ],
)
def test_cron_expressions(project_id, cron, expected):
    assert schedules_processor._replace_extended_cron_pattern(project_id, cron) == expected


def test_invalid_cron_expression():
    with pytest.raises(ValueError) as exc_info:
        schedules_processor.ExtendedCronPattern(1, "* * *")
    assert str(exc_info.value) == str(ValueError("Expected 5 parts in the cron expression, got ['*', '*', '*']"))
