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
            variables:
              secret1:
                key: foo
                value: bar

          "some_group/*":
            variables:
              secret2:
                key: foo
                value: bar

          "some_group/my_project":
            variables:
              inherit: false
              secret3:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/my_project")

        variables = effective_config["variables"]

        assert variables == {
            "secret3": {"key": "bizz", "value": "buzz"},
        }

    def test__inheritance_break__flag_set_at_project_level__project_inherits_group_and_not_common(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              secret1:
                key: foo
                value: bar

          "some_group/*":
            members:
              users:
                user1: developer
                user2: developer

          "some_group/my_project":
            variables:
              inherit: false
              secret2:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/my_project")

        assert effective_config == {
            "members": {
                "users": {
                    "user1": "developer",
                    "user2": "developer",
                }
            },
            "variables": {
                "secret2": {"key": "bizz", "value": "buzz"},
            },
        }

    def test__inheritance_break__flag_set_at_group_level__group_inherits_nothing(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              secret1:
                key: foo
                value: bar

          "some_group/*":
            variables:
              inherit: false
              secret2:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group")

        variables = effective_config["variables"]

        assert variables == {
            "secret2": {"key": "foo", "value": "bar"},
        }

    def test__inheritance_break__flag_set_at_group_level__project_inherits_group_and_not_common(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              secret1:
                key: foo
                value: bar

          "some_group/*":
            variables:
              inherit: false
              secret2:
                key: foo
                value: bar

          "some_group/my_project":
            variables:
              secret3:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/my_project")

        variables = effective_config["variables"]

        assert variables == {
            "secret2": {"key": "foo", "value": "bar"},
            "secret3": {"key": "bizz", "value": "buzz"},
        }

    def test__inheritance_break__flag_set_at_group_level_and_project_level__project_inherits_nothing(
        self,
    ):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            variables:
              secret1:
                key: foo
                value: bar

          "some_group/*":
            variables:
              inherit: false
              secret2:
                key: foo
                value: bar

          "some_group/my_project":
            variables:
              inherit: false
              secret3:
                key: bizz
                value: buzz
        """

        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/my_project")

        variables = effective_config["variables"]

        assert variables == {
            "secret3": {"key": "bizz", "value": "buzz"},
        }
