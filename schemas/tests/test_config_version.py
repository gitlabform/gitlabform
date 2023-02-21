import jsonschema
import yaml
import pytest
import textwrap
from jsonschema.exceptions import SchemaError, ValidationError


class TestConfigVersion:
    schema_id: str = "https://raw.githubusercontent.com/gitlabform/gitlabform/main/schemas/properties/config_version.json"
    test_data: list[tuple[str, type[ValidationError] | None]] = [
        (
            f"""
                1
            """,
            ValidationError,
        ),
        (
            f"""
                2
            """,
            ValidationError,
        ),
        (
            f"""
                3
            """,
            None,
        ),
        (
            f"""
                3.0
            """,
            None,
        ),
        (
            f"""
                3.5
            """,
            ValidationError,
        ),
        (
            f"""
                3.x
            """,
            ValidationError,
        ),
        (
            f"""
                config_version: 3
            """,
            ValidationError,
        ),
    ]

    @pytest.mark.dependency()
    def test__validate_config_version_schema(self, get_schema_validator):
        validator = get_schema_validator(self.schema_id)

        try:
            validator.check_schema(validator.schema)
        except SchemaError as error:
            assert False, f"Schema is invalid: {error.message} - {error.json_path}"

    @pytest.mark.dependency(
        depends=["TestConfigVersion::test__validate_config_version_schema"]
    )
    @pytest.mark.parametrize("config_yaml, expected_error", test_data)
    def test__config_of_config_version_schema(
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
