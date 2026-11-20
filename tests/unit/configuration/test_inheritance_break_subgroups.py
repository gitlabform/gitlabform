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

    def test__inheritance_break__flag_inherited_from_wildcard_ancestor_does_not_abort_subgroup_lookup(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            merge_requests_approval_rules:
              some_rule:
                approvals_required: 1
          acme/*:
            merge_requests_approval_rules:
              inherit: false
              override_rule:
                approvals_required: 2
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("acme/tools")

        assert effective_config == {
            "merge_requests_approval_rules": {
                "override_rule": {"approvals_required": 2},
            },
        }


class TestInheritanceBreakBlocksCommon:
    @pytest.fixture
    def configuration_with_break_at_subgroup_and_common(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            group_settings:
              from_common: true
            project_settings:
              common_project_setting: true
          some_group/*:
            group_settings:
              from_recursive: true
          some_group/subgroup/*:
            group_settings:
              inherit: false
              visibility: public
        """
        return Configuration(config_string=config_yaml)

    def test__inheritance_break__subgroup_break_blocks_common(self, configuration_with_break_at_subgroup_and_common):
        effective_config = configuration_with_break_at_subgroup_and_common.get_effective_config_for_group(
            "some_group/subgroup"
        )

        assert effective_config["group_settings"] == {"visibility": "public"}

    def test__inheritance_break__subgroup_break_only_affects_its_section(
        self, configuration_with_break_at_subgroup_and_common
    ):
        effective_config = configuration_with_break_at_subgroup_and_common.get_effective_config_for_group(
            "some_group/subgroup"
        )

        assert effective_config["project_settings"] == {"common_project_setting": True}

    def test__inheritance_break__project_in_breaking_subgroup_does_not_get_common(
        self, configuration_with_break_at_subgroup_and_common
    ):
        effective_config = configuration_with_break_at_subgroup_and_common.get_effective_config_for_project(
            "some_group/subgroup/some_project"
        )

        assert effective_config["group_settings"] == {"visibility": "public"}

    def test__inheritance_break__deep_subgroup_below_break_does_not_get_common(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            group_settings:
              from_common: true
          a/*:
            group_settings:
              from_a: true
          a/b/*:
            group_settings:
              inherit: false
              x: 1
          a/b/c/*:
            group_settings:
              y: 2
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("a/b/c")

        assert effective_config["group_settings"] == {"x": 1, "y": 2}

    def test__inheritance_break__nested_key_break_at_subgroup_level_blocks_common(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            merge_requests_approval_rules:
              some_rule:
                approvals_required: 1
                name: common
              other_rule:
                approvals_required: 3
          acme/*:
            merge_requests_approval_rules:
              some_rule:
                name: acme
          acme/tools/*:
            merge_requests_approval_rules:
              some_rule:
                inherit: false
                approvals_required: 2
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("acme/tools")

        assert effective_config["merge_requests_approval_rules"] == {
            "some_rule": {"approvals_required": 2},
            "other_rule": {"approvals_required": 3},
        }

    def test__effective_config_for_group_without_own_layers_is_a_copy_of_common(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            group_badges:
              enforce: true
          other_group/*:
            group_settings:
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        lonely_group_config = configuration.get_effective_config_for_group("lonely_group")
        lonely_group_config["group_badges"].pop("enforce")

        assert configuration.get_effective_config_for_group("other_group")["group_badges"] == {"enforce": True}
