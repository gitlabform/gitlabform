from gitlabform.processors import AbstractProcessor
from gitlabform.gitlab import GitLab
from unittest.mock import MagicMock


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


class TestGetGitlabVersion:

    version_to_expected_map = {
        "15.6.4-ee": (15, 6),
        "unknown": (0, 0),
    }

    class TestAbstractProcessor(AbstractProcessor):
        __test__ = False

        def __init__(self, gitlab: GitLab):
            self.gitlab = gitlab

        def _process_configuration(self, project_or_project_and_group: str, configuration: dict):
            pass

    def test__get_gitlab_server_version(self) -> None:
        gitlab = MagicMock(GitLab)
        processor = self.TestAbstractProcessor(gitlab)
        processor.gitlab = gitlab

        for version, expected in self.version_to_expected_map.items():
            gitlab.version = version
            assert processor._get_gitlab_server_version() == expected
