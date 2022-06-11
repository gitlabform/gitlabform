import logging

from gitlabform.configuration import Configuration

logger = logging.getLogger(__name__)


class TestInheritanceBreakProjectsAndGroups:
    def test__inheritance_break__flag_set_at_project_level__project_inherits_nothing(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            secret_variables:
              third:
                key: foo
                value: bar
    
          "some_group/*":
            secret_variables:
              first:
                key: foo
                value: bar
    
          "some_group/my_project":
            secret_variables:
              inherit: false
              second:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project(
            "some_group/my_project"
        )

        secret_variables = effective_config["secret_variables"]

        assert secret_variables == {
            "second": {"key": "bizz", "value": "buzz"},
        }

    def test__inheritance_break__flag_set_at_group_level__project_inherits_group_and_not_common(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            secret_variables:
              third:
                key: foo
                value: bar
    
          "some_group/*":
            secret_variables:
              inherit: false
              first:
                key: foo
                value: bar
    
          "some_group/my_project":
            secret_variables:
              second:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project(
            "some_group/my_project"
        )

        secret_variables = effective_config["secret_variables"]

        assert secret_variables == {
            "first": {"key": "foo", "value": "bar"},
            "second": {"key": "bizz", "value": "buzz"},
        }

    def test__inheritance_break__flag_set_at_project_level__project_inherits_group_and_not_common(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            secret_variables:
              third:
                key: foo
                value: bar
    
          "some_group/*":
            members:
              users:
                user1: developer
                user2: developer
    
          "some_group/my_project":
            secret_variables:
              inherit: false
              second:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project(
            "some_group/my_project"
        )

        assert effective_config == {
            "members": {
                "users": {
                    "user1": "developer",
                    "user2": "developer",
                }
            },
            "secret_variables": {
                "second": {"key": "bizz", "value": "buzz"},
            },
        }
