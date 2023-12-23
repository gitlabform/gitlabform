import datetime

from gitlabform.util import to_str


def test_date_stringification():
    example_project_config = {
        "members": {
            "enforce": True,
            "users": {
                "project_204_bot": {"access_level": 40},
                "project_204_bot_211c9f071a88910e7ed518cc5d81436a": {
                    "access_level": 40,
                    "expires_at": datetime.date(2024, 12, 12),
                },
            },
        }
    }
    output = to_str(example_project_config)
    assert type(output) is str
