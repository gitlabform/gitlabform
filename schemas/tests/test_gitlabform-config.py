import jsonschema
import yaml
import pytest
import textwrap
from jsonschema.exceptions import SchemaError, ValidationError


class TestGitLabFormConfig:
    schema_id: str = "https://raw.githubusercontent.com/gitlabform/gitlabform/main/schemas/gitlabform.json"
    test_data: list[tuple[str, type[ValidationError] | None]] = [
        (
            f"""
                config_version: 3
                gitlab:
                  url: http://localhost
                skip_projects:
                  - group-one/project-one
                  - group-two/*
                skip_groups:
                  - group-three/subgroup-one
                  - group-four/*
            """,
            None,
        ),
        (
            f"""
                config_version: 3
                projects: &projects-to-skip
                  - group-one/project-one
                  - group-two/project-one
                skip_projects: *projects-to-skip
            """,
            None,
        ),
        # This one should fail because config_version is require property but doesn't exist
        (
            f"""
                gitlab:
                  url: http://localhost
            """,
            ValidationError,
        ),
        # This one should fail because skip_groups is not an array
        (
            f"""
                config_version: 3
                projects: &projects-to-skip
                  - group-one/project-one
                  - group-two/project-one
                skip_projects: *projects-to-skip
                skip_groups: group-three
            """,
            ValidationError,
        ),
    ]

    @pytest.mark.dependency()
    def test__validate_gitlabform_schema(self, get_schema_validator):
        validator = get_schema_validator(self.schema_id)

        try:
            validator.check_schema(validator.schema)
        except SchemaError as error:
            assert False, f"Schema is invalid: {error.message} - {error.json_path}"

    @pytest.mark.dependency(
        depends=["TestGitLabFormConfig::test__validate_gitlabform_schema"]
    )
    @pytest.mark.parametrize("config_yaml, expected_error", test_data)
    def test__config_of_gitlabform_schema(
        self, get_schema_validator, config_yaml, expected_error
    ):
        validator = get_schema_validator(self.schema_id)
        # f-strings with """ used as configs have the disadvantage of having indentation in them - let's remove it here
        config = textwrap.dedent(config_yaml)

        gitlabform_config = yaml.safe_load(config)

        try:
            validation_result = validator.validate(instance=gitlabform_config)
            assert (
                validation_result == expected_error
            ), f"Config is invalid: {gitlabform_config}"
        except ValidationError as error:
            assert (
                expected_error == ValidationError
            ), f"Invalid config found as expected: {error.message}"
