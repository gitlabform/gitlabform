import pytest
import json
import jsonschema
from pathlib import Path
from jsonschema.protocols import Validator
from referencing import Resource, Registry
from typing import Callable, Generator


@pytest.fixture(scope="session")
def schema_registry() -> Generator[Registry, None, None]:
    SCHEMA_DIR: Path = Path.cwd() / "schemas/src"
    schema_registry: Registry = Registry()

    schema_registry = [
        Resource.from_contents(json.loads(schema_file.read_text()))
        for schema_file in SCHEMA_DIR.glob("**/*.json")
    ] @ schema_registry

    schema_registry = schema_registry.crawl()

    yield schema_registry


@pytest.fixture(scope="function")
def get_schema_validator(
    schema_registry: Registry,
) -> Generator[Callable[[str], Validator], None, None]:
    def _get_schema_validator(schema_id: str) -> Validator:
        schema = schema_registry.get_or_retrieve(schema_id).value.contents
        validator_class = jsonschema.validators.validator_for(schema)
        validator = validator_class(schema=schema, registry=schema_registry)

        return validator

    yield _get_schema_validator
