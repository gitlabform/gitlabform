import pytest

from gitlabform.configuration import Configuration


@pytest.fixture
def yaml11_configuration_with_yes():
    config_yaml = """
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: yes          # in YAML 1.1 this should be interpreted as boolean true
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def yaml12_configuration():
    config_yaml = """
    %YAML 1.2
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: true
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def yaml11_annotated_configuration_with_yes():
    config_yaml = """
    %YAML 1.1
    ---
    projects_and_groups:
      some_group/*:
        project_settings:
          foo: yes          # in YAML 1.1 this should be interpreted as boolean true
    """
    return Configuration(config_string=config_yaml)


def test__unannotated_yaml_11(yaml11_configuration_with_yes):
    """
    By default, in v6.+ we use YAML 1.2, so the "yes" value is not interpreted as a boolean.
    This test validates that without annotation, the YAML file is treated as v1.2, and "yes" is just a string, not a boolean.
    """
    assert yaml11_configuration_with_yes.get("projects_and_groups|some_group/*|project_settings") == {"foo": "yes"}


def test__annotated_yaml_11(yaml11_annotated_configuration_with_yes):
    """
    By default, in v6.+ we use YAML 1.2, so the "yes" value is not interpreted as a boolean, unless annotated as such.
    This test validates the annotation can correctly set a YAML file to v1.1
    """
    assert yaml11_annotated_configuration_with_yes.get("projects_and_groups|some_group/*|project_settings") == {
        "foo": True
    }


def test__yaml_12(yaml12_configuration):
    assert yaml12_configuration.get("projects_and_groups|some_group/*|project_settings") == {"foo": True}
