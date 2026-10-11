import pytest

from gitlabform.configuration import Configuration
from gitlabform.constants import EXIT_INVALID_INPUT


def test__env_tag_resolves_value_from_environment_variable(monkeypatch):
    monkeypatch.setenv("GITLABFORM_TEST_TOKEN", "s3cr3t")

    config_yaml = """
    projects_and_groups:
      foo/bar:
        pull_mirror:
          url: https://example.com/repo.git
          auth_password: !env GITLABFORM_TEST_TOKEN
    """

    configuration = Configuration(config_string=config_yaml)

    effective = configuration.get_effective_config_for_project("foo/bar")
    assert effective["pull_mirror"]["auth_password"] == "s3cr3t"


def test__env_tag_missing_environment_variable_aborts(monkeypatch):
    monkeypatch.delenv("GITLABFORM_TEST_MISSING", raising=False)

    config_yaml = """
    projects_and_groups:
      foo/bar:
        pull_mirror:
          auth_password: !env GITLABFORM_TEST_MISSING
    """

    with pytest.raises(SystemExit) as e:
        Configuration(config_string=config_yaml)

    assert e.value.code == EXIT_INVALID_INPUT


def test__env_tag_without_variable_name_aborts():
    config_yaml = """
    projects_and_groups:
      foo/bar:
        pull_mirror:
          auth_password: !env
    """

    with pytest.raises(SystemExit) as e:
        Configuration(config_string=config_yaml)

    assert e.value.code == EXIT_INVALID_INPUT


def test__env_tag_is_not_registered_on_ruamel_globally(monkeypatch):
    # gitlabform can be used as a library; its custom tag must not change
    # how other code in the process parses YAML
    from ruamel.yaml import YAML

    monkeypatch.setenv("GITLABFORM_TEST_TOKEN", "s3cr3t")
    Configuration(config_string="projects_and_groups: {}")

    data = YAML().load("value: !env GITLABFORM_TEST_TOKEN")

    assert data["value"] != "s3cr3t"
    assert str(data["value"].tag) == "!env"


def test__values_without_env_tag_stay_literal(monkeypatch):
    monkeypatch.setenv("GITLABFORM_TEST_TOKEN", "s3cr3t")

    config_yaml = """
    projects_and_groups:
      foo/bar:
        project_variables:
          some_var:
            key: SOME_VAR
            value: "$GITLABFORM_TEST_TOKEN and ${GITLABFORM_TEST_TOKEN}"
    """

    configuration = Configuration(config_string=config_yaml)

    effective = configuration.get_effective_config_for_project("foo/bar")
    assert effective["project_variables"]["some_var"]["value"] == "$GITLABFORM_TEST_TOKEN and ${GITLABFORM_TEST_TOKEN}"
