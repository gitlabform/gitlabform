import yaml
import pytest
import textwrap
from jsonschema.exceptions import SchemaError, ValidationError


class TestGitlab:
    schema_id: str = "https://raw.githubusercontent.com/gitlabform/gitlabform/main/schemas/properties/gitlab.json"
    test_data: list[tuple[str, type[ValidationError] | None]] = [
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-123
                ssl_verify: true
                timeout: 20
            """,
            None,
        ),
        (
            f"""
                url: https://localhost
                token: glpat-1234567890-123
                ssl_verify: true
                timeout: 20
            """,
            None,
        ),
        # This one should fail because URL value doesn't match pattern
        (
            f"""
                url: localhost
                token: glpat-1234567890-123
                ssl_verify: true
                timeout: 20
            """,
            ValidationError,
        ),
        # This one should fail because token value is shorter than 20 characters
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-12
                ssl_verify: true
                timeout: 20
            """,
            ValidationError,
        ),
        # This one should fail because token value is longer than 20 characters
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-1234
                ssl_verify: true
                timeout: 20
            """,
            ValidationError,
        ),
        # This should fail because ssl_verify is not boolean
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-123
                ssl_verify: "true"
                timeout: 20
            """,
            ValidationError,
        ),
        # This one should fail because timeout is not integer
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-123
                ssl_verify: true
                timeout: "20"
            """,
            ValidationError,
        ),
        # This one should fail because additional properties are not allowed
        (
            f"""
                url: http://localhost
                token: glpat-1234567890-123
                ssl_verify: true
                timeout: 20
                foo: bar
            """,
            ValidationError,
        ),
    ]

    @pytest.mark.dependency()
    def test__validate_gitlab_schema(self, get_schema_validator):
        validator = get_schema_validator(self.schema_id)

        try:
            validator.check_schema(validator.schema)
        except SchemaError as error:
            assert False, f"Schema is invalid: {error.message} - {error.json_path}"

    @pytest.mark.dependency(depends=["TestGitlab::test__validate_gitlab_schema"])
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
