import logging
import pytest

from gitlabform.configuration import Configuration
from gitlabform import EXIT_INVALID_INPUT

logger = logging.getLogger(__name__)


class TestInheritanceBreakValidation:
    def test__validate_break_inheritance_flag__valid_flag_set_at_group_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            secret_variables:
              first:
                key: foo
                value: bar
        """

        group_name = "some_group"
        configuration = Configuration(config_string=config_yaml).get_group_config(
            group_name
        )
        Configuration.validate_break_inheritance_flag(configuration, group_name)

    def test__validate_break_inheritance_flag__valid_flag_set_at_project_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          "some_group/some_project":
            secret_variables:
              foo: bar
        """

        group_and_project_name = "some_group/some_project"
        configuration = Configuration(config_string=config_yaml).get_project_config(
            group_and_project_name
        )
        Configuration.validate_break_inheritance_flag(
            configuration, group_and_project_name
        )

    def test__validate_break_inheritance_flag__invalid_flag_set_at_common_level(self):
        config_yaml = """
            ---
            projects_and_groups:
              "*":
                inherit: false
                secret_variables:
                  first:
                    key: foo
                    value: bar
            """

        common_key = "*"
        configuration = Configuration(config_string=config_yaml).get_common_config()
        with pytest.raises(SystemExit) as exception:
            Configuration.validate_break_inheritance_flag(configuration, common_key)
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__invalid_flag_set_at_group_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            secret_variables:
              inherit: false
              first:
                key: foo
                value: bar
        """

        group_name = "some_group"
        configuration = Configuration(config_string=config_yaml).get_group_config(
            group_name
        )
        with pytest.raises(SystemExit) as exception:
            Configuration.validate_break_inheritance_flag(configuration, group_name)
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__invalid_flag_set_at_project_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          "some_group/some_project":
            secret_variables:
              inherit: false
              foo: bar
        """

        group_and_project_name = "some_group/some_project"
        configuration = Configuration(config_string=config_yaml).get_project_config(
            group_and_project_name
        )
        with pytest.raises(SystemExit) as exception:
            Configuration.validate_break_inheritance_flag(
                configuration, group_and_project_name
            )
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_break_inheritance_flag__valid_flag_set_at_subgroup_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/subgroup/*:
            group_members:
              my-user:
                access_level: 10
        """

        subgroup_name = "some_group/subgroup"
        configuration = Configuration(config_string=config_yaml).get_group_config(
            subgroup_name
        )
        Configuration.validate_break_inheritance_flag(configuration, subgroup_name)

    def test__validate_break_inheritance_flag__invalid_flag_set_at_subgroup_level(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/subgroup/*:
            group_members:
              inherit: false
              my-user:
                access_level: 10
        """

        subgroup_name = "some_group/subgroup"
        configuration = Configuration(config_string=config_yaml).get_group_config(
            subgroup_name
        )
        with pytest.raises(SystemExit) as exception:
            Configuration.validate_break_inheritance_flag(configuration, subgroup_name)
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT
