from gitlabform.configuration import Configuration


class TestPropagationBreakGroupsAndProjects:
    def test__propagation_break__flag_set_at_group_level__subgroup_does_not_inherit_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              secret1:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group/some_subgroup")

        assert effective_config == {}

    def test__propagation_break__flag_set_at_group_level__project_does_not_inherit_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              secret1:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/some_project")

        assert effective_config == {}

    def test__propagation_break__flag_set_at_group_level__group_still_gets_its_own_section(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              secret1:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group")

        assert effective_config == {
            "variables": {
                "secret1": {
                    "key": "foo",
                    "value": "bar",
                }
            }
        }

    def test__propagation_break__common_level_flag_blocks_global_inheritance_until_local_redefinition(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              propagate: false
              global_secret:
                key: foo
                value: bar

          some_group/*:
            variables:
              local_secret:
                key: fizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_group_config = configuration.get_effective_config_for_group("some_group")
        effective_project_config = configuration.get_effective_config_for_project("some_group/some_project")

        expected_variables = {
            "local_secret": {
                "key": "fizz",
                "value": "buzz",
            }
        }

        assert effective_group_config == {"variables": expected_variables}
        assert effective_project_config == {"variables": expected_variables}

    def test__propagation_break__common_level_flag_blocks_groups_and_projects_without_local_redefinition(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              propagate: false
              global_secret:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        effective_group_config = configuration.get_effective_config_for_group("some_group")
        effective_project_config = configuration.get_effective_config_for_project("some_group/some_project")

        assert effective_group_config == {}
        assert effective_project_config == {}

    def test__propagation_break__common_level_local_redefinition_in_subgroup_reopens_for_deeper_project(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              propagate: false
              global_secret:
                key: foo
                value: bar

          some_group/some_subgroup/*:
            variables:
              subgroup_secret:
                key: fizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/some_subgroup")
        effective_project_config = configuration.get_effective_config_for_project(
            "some_group/some_subgroup/some_project"
        )

        expected_variables = {
            "subgroup_secret": {
                "key": "fizz",
                "value": "buzz",
            }
        }

        assert effective_subgroup_config == {"variables": expected_variables}
        assert effective_project_config == {"variables": expected_variables}

    def test__propagation_break__local_redefinition_reopens_propagation_for_descendants(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              secret1:
                key: foo
                value: bar

          some_group/some_subgroup/*:
            variables:
              secret2:
                key: fizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/some_subgroup")
        effective_project_config = configuration.get_effective_config_for_project(
            "some_group/some_subgroup/some_project"
        )

        expected_variables = {
            "secret2": {
                "key": "fizz",
                "value": "buzz",
            }
        }

        assert effective_subgroup_config == {"variables": expected_variables}
        assert effective_project_config == {"variables": expected_variables}

    def test__propagation_break__skip_alone_does_not_reopen_propagation(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: false
              secret1:
                key: foo
                value: bar

          some_group/some_subgroup/*:
            variables:
              skip: true
        """

        configuration = Configuration(config_string=config_yaml)

        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/some_subgroup")
        effective_project_config = configuration.get_effective_config_for_project(
            "some_group/some_subgroup/some_project"
        )

        assert effective_subgroup_config == {"variables": {"skip": True}}
        assert effective_project_config == {}

    def test__propagation_break__skip_only_affects_current_entity_when_section_is_not_blocked(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              secret1:
                key: foo
                value: bar

          some_group/some_subgroup/*:
            variables:
              skip: true
        """

        configuration = Configuration(config_string=config_yaml)

        effective_subgroup_config = configuration.get_effective_config_for_group("some_group/some_subgroup")
        effective_project_config = configuration.get_effective_config_for_project(
            "some_group/some_subgroup/some_project"
        )

        assert effective_subgroup_config == {"variables": {"secret1": {"key": "foo", "value": "bar"}, "skip": True}}
        assert effective_project_config == {"variables": {"secret1": {"key": "foo", "value": "bar"}}}
