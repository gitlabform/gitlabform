import pytest

from gitlabform.configuration import Configuration
from gitlabform import EXIT_INVALID_INPUT



class TestInheritanceBreakValidation:
    def test__validate_break_inheritance_flag__invalid_flag_set_at_common_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            inherit: false
            secret_variables:
              secret:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_common_config()
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__invalid_flag_set_at_project_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          "some_group/some_project":
            secret_variables:
              inherit: false
              secret:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_project("some_group/some_project")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__get_config_for_group__invalid_flag_set_at_group_level(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            group_members:
              enforce: true
              users:
                inherit: false
                my-user:
                  access_level: maintainer
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_group("some_group")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__get_config_for_project__invalid_flag_set_at_group_level(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            members:
              enforce: true
              users:
                inherit: false
                my-user:
                  access_level: maintainer
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_project("some_group/*")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__get_config_for_group__invalid_flag_set_at_subgroup_level(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/subgroup1/*:
            members:
              enforce: true
              users:
                inherit: false
                my-user:
                  access_level: maintainer
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_group("some_group/subgroup1")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__get_config_for_project__invalid_flag_set_at_subgroup_level(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/subgroup1/subgroup2/*:
            members:
              enforce: true
              users:
                inherit: false
                my-user:
                  access_level: maintainer
        """

        configuration = Configuration(config_string=config_yaml)
        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_project("some_group/subgroup1/subgroup2/*")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT
