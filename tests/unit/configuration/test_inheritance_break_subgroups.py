import pytest

from gitlabform.configuration import Configuration


class TestInheritanceBreakSubgroups:
    def test__inheritance_break__flag_set_at_subgroup_level__subgroup_inherits_nothing(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            project_settings:
              foo: bar
    
          some_group/some_subgroup/*:
            project_settings:
              inherit: false
              fizz: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group/some_subgroup")

        assert effective_config == {
            "project_settings": {"fizz": "buzz"},
        }

    @pytest.fixture
    def configuration_with_inheritance_break_set_at_subgroup_and_project_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            group_settings:
              snap: crackle
            project_settings:
              foo: bar

          some_group/subgroup_level_1/*:
            group_settings:
              inherit: false
              crackle: pop
            project_settings:
              foo1: bar1
              
          some_group/subgroup_level_1/some_project:
            project_settings:
              inherit: false
              fizz: buzz

          some_group/subgroup_level_1/subgroup_level_2/*:
            project_settings:
              inherit: false
              foo2: bar2

          some_group/subgroup_level_1/subgroup_level_2/some_project:
            group_settings:
              inherit: false
              snap: pop
            project_settings:
              inherit: false
              fizz: buzz
        """
        return Configuration(config_string=config_yaml)

    def test__inheritance_break__flag_set_at_subgroup_level__first_subgroup_does_not_inherit_group_settings(
        self,
        configuration_with_inheritance_break_set_at_subgroup_and_project_level,
    ):
        effective_config = (
            configuration_with_inheritance_break_set_at_subgroup_and_project_level.get_effective_config_for_group(
                "some_group/subgroup_level_1"
            )
        )

        assert effective_config == {
            "group_settings": {"crackle": "pop"},
            "project_settings": {
                "foo": "bar",
                "foo1": "bar1",
            },
        }

    def test__inheritance_break__flag_set_at_project_level__first_subgroup_project_does_not_inherit_project_settings(
        self,
        configuration_with_inheritance_break_set_at_subgroup_and_project_level,
    ):
        effective_config = (
            configuration_with_inheritance_break_set_at_subgroup_and_project_level.get_effective_config_for_project(
                "some_group/subgroup_level_1/some_project"
            )
        )

        assert effective_config == {
            "group_settings": {"crackle": "pop"},
            "project_settings": {
                "fizz": "buzz",
            },
        }

    def test__inheritance_break__flag_set_at_subgroup_level__second_subgroup_does_not_inherit_project_settings(
        self,
        configuration_with_inheritance_break_set_at_subgroup_and_project_level,
    ):
        effective_config = (
            configuration_with_inheritance_break_set_at_subgroup_and_project_level.get_effective_config_for_group(
                "some_group/subgroup_level_1/subgroup_level_2"
            )
        )

        assert effective_config == {
            "group_settings": {"crackle": "pop"},
            "project_settings": {
                "foo2": "bar2",
            },
        }

    def test__inheritance_break__flag_set_at_project_level__second_subgroup_project_inherits_nothing(
        self,
        configuration_with_inheritance_break_set_at_subgroup_and_project_level,
    ):
        effective_config = (
            configuration_with_inheritance_break_set_at_subgroup_and_project_level.get_effective_config_for_project(
                "some_group/subgroup_level_1/subgroup_level_2/some_project"
            )
        )

        assert effective_config == {
            "group_settings": {"snap": "pop"},
            "project_settings": {
                "fizz": "buzz",
            },
        }
