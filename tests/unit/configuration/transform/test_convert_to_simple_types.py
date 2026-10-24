from gitlabform.configuration import Configuration
from gitlabform.configuration.transform import ConfigurationTransformer

LONG_REGEX = "^(feat|fix|chore|docs|refactor|test|ci|build|perf)(\\([^)]+\\))?!?: [A-Z][A-Z0-9]{1,9}-\\d+ .+"


def test__convert_to_simple_types_keeps_long_regex_with_escapes_intact() -> None:
    config_yaml = f"""
    projects_and_groups:
      "foo/bar":
        project_settings:
          merge_request_title_regex: "{LONG_REGEX.replace(chr(92), chr(92) * 2)}"
    """
    configuration = Configuration(config_string=config_yaml)

    ConfigurationTransformer.convert_to_simple_types(configuration)

    project_settings = configuration.config["projects_and_groups"]["foo/bar"]["project_settings"]
    assert project_settings["merge_request_title_regex"] == LONG_REGEX
