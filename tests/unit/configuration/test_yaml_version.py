import pytest

from gitlabform.configuration import Configuration


@pytest.fixture
def configuration_with_yes():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: yes          # in YAML 1.1 this should be interpreted as boolean true
    """
    return Configuration(config_string=config_yaml)


def test__default_yaml_11(configuration_with_yes):
    assert configuration_with_yes.get("projects_and_groups|some_group/*|project_settings") == {"foo": True}
