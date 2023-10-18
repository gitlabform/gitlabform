import jsonschema
import yaml
import pytest
import textwrap
from jsonschema.exceptions import SchemaError, ValidationError


class TestSkipGroups:
    schema_id: str = "https://raw.githubusercontent.com/gitlabform/gitlabform/main/schemas/properties/skip_groups.json"
    test_data: list[tuple[str, type[ValidationError] | None]] = [
        (
            f"""
                - foo
                - bar
            """,
            None,
        ),
        (
            f"""
                - group-one/subgroup/*
                - group-two/subgroup/sub-subgroup
            """,
            None,
        ),
        # This one should fail because at least one item is required
        (
            f"""
                []
            """,
            ValidationError,
        ),
        # This one should fail because duplicate entries are not allowed
        (
            f"""
                - group-one/subgroup/*
                - group-one/subgroup/*
            """,
            ValidationError,
        ),
        # This one should fail because empty value is not allowed
        (
            f"""
                - ""
            """,
            ValidationError,
        ),
        # This one should fail because it's not an array
        (
            f"""
                2
            """,
            ValidationError,
        ),
        # This one should fail because it's not an array
        (
            f"""
                foo
            """,
            ValidationError,
        ),
        # This one should fail because it's not an array
        (
            f"""
                foo: bar
            """,
            ValidationError,
        ),
        # This one should fail becaue it's not an array
        (
            f"""
                groups:
                  - group-one
                  - group-two
            """,
            ValidationError,
        ),
        # This one should fail because one of the item in the array contains non-string value
        (
            f"""
                - group-one/subgroup/*
                - group-two/subgroup/sub-subgroup
                - foo:
                    key: value
            """,
            ValidationError,
        ),
    ]

    @pytest.mark.dependency()
    def test__validate_skip_group_schema(self, get_schema_validator):
        validator = get_schema_validator(self.schema_id)

        try:
            validator.check_schema(validator.schema)
        except SchemaError as error:
            assert False, f"Schema is invalid: {error.message} - {error.json_path}"

    @pytest.mark.dependency(
        depends=["TestSkipGroups::test__validate_skip_group_schema"]
    )
    @pytest.mark.parametrize("config_yaml, expected_error", test_data)
    def test__config_of_skip_groups_schema(
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
