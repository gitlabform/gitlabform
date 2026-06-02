import pytest

from gitlabform import EXIT_INVALID_INPUT
from gitlabform.configuration import Configuration


class TestPropagationBreakValidation:
    def test__validate_propagation_break_flag__true_value_is_invalid(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: true
              secret:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_group("some_group")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT

    def test__validate_propagation_break_flag__scalar_value_is_invalid(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            variables:
              propagate: 1
              secret:
                key: foo
                value: bar
        """

        configuration = Configuration(config_string=config_yaml)

        with pytest.raises(SystemExit) as exception:
            configuration.get_effective_config_for_group("some_group")
        assert exception.type == SystemExit
        assert exception.value.code == EXIT_INVALID_INPUT
