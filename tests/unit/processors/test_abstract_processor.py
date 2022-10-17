from gitlabform.processors import AbstractProcessor


class TestRecursiveDiffAnalyzer:
    # TODO: user (instead of user_id)
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

    _cfg_b = [{"access_level": 40, "group_inheritance_type": 0}, {"user_id": 967}]

    def test_equal_configurations(self):
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

        assert not AbstractProcessor.recursive_diff_analyzer(
            "deploy_access_levels", self._cfg_a, self._cfg_b
        )

    def test_unequal_configurations(self):
        modified_cfg = self._cfg_b.copy()

        modified_cfg[1]["group_inheritance_type"] = 1

        assert AbstractProcessor.recursive_diff_analyzer(
            "deploy_access_levels", self._cfg_a, modified_cfg
        )
