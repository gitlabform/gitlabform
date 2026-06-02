from gitlabform.configuration import Configuration


class TestPropagationBreakSubgroups:
    def test__propagation_break__flag_set_at_subgroup_level__deeper_subgroup_does_not_inherit_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            project_settings:
              root: value

          some_group/some_subgroup/*:
            project_settings:
              propagate: false
              subgroup: value
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group/some_subgroup/deeper_subgroup")

        assert effective_config == {}

    def test__propagation_break__flag_set_at_subgroup_level__deeper_project_does_not_inherit_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            project_settings:
              root: value

          some_group/some_subgroup/*:
            project_settings:
              propagate: false
              subgroup: value
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/some_subgroup/some_project")

        assert effective_config == {}

    def test__propagation_break__inherit_and_propagate_can_coexist_on_same_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              common_secret:
                key: foo
                value: bar

          some_group/*:
            variables:
              inherit: false
              propagate: false
              group_secret:
                key: fizz
                value: buzz

          some_group/some_subgroup/*:
            variables:
              subgroup_secret:
                key: zap
                value: zip
        """

        configuration = Configuration(config_string=config_yaml)

        effective_group_config = configuration.get_effective_config_for_group("some_group")
        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/some_subgroup")
        effective_project_config = configuration.get_effective_config_for_project(
            "some_group/some_subgroup/some_project"
        )

        assert effective_group_config == {
            "variables": {
                "group_secret": {
                    "key": "fizz",
                    "value": "buzz",
                }
            }
        }
        assert effective_subgroup_config == {
            "variables": {
                "subgroup_secret": {
                    "key": "zap",
                    "value": "zip",
                }
            }
        }
        assert effective_project_config == {
            "variables": {
                "subgroup_secret": {
                    "key": "zap",
                    "value": "zip",
                }
            }
        }

    def test__propagation_break__descendant_local_redefinition_reopens_for_deeper_subtree(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              root_secret:
                key: ROOT_SECRET
                value: root-value

          some_group/subgroup_level_1/*:
            variables:
              subgroup_secret:
                key: SUBGROUP_SECRET
                value: subgroup-value
        """

        configuration = Configuration(config_string=config_yaml)

        effective_deeper_subgroup_config = configuration.get_effective_config_for_group(
            "some_group/subgroup_level_1/subgroup_level_2"
        )
        effective_deeper_project_config = configuration.get_effective_config_for_project(
            "some_group/subgroup_level_1/subgroup_level_2/some_project"
        )

        expected_variables = {
            "subgroup_secret": {
                "key": "SUBGROUP_SECRET",
                "value": "subgroup-value",
            }
        }

        assert effective_deeper_subgroup_config == {"variables": expected_variables}
        assert effective_deeper_project_config == {"variables": expected_variables}

    def test__propagation_break__descendant_redefinition_can_block_again_for_its_own_descendants(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              root_secret:
                key: ROOT_SECRET
                value: root-value

          some_group/subgroup_level_1/*:
            variables:
              propagate: false
              subgroup_secret:
                key: SUBGROUP_SECRET
                value: subgroup-value
        """

        configuration = Configuration(config_string=config_yaml)

        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/subgroup_level_1")
        effective_deeper_subgroup_config = configuration.get_effective_config_for_group(
            "some_group/subgroup_level_1/subgroup_level_2"
        )
        effective_deeper_project_config = configuration.get_effective_config_for_project(
            "some_group/subgroup_level_1/subgroup_level_2/some_project"
        )

        assert effective_subgroup_config == {
            "variables": {
                "subgroup_secret": {
                    "key": "SUBGROUP_SECRET",
                    "value": "subgroup-value",
                }
            }
        }
        assert effective_deeper_subgroup_config == {}
        assert effective_deeper_project_config == {}
