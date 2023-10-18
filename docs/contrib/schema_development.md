# Schema Development

Schemas for GitLabForm's configuration syntax is written using [JSON Schema](https://json-schema.org/).

The `schemas/src/` directory contains various independent schemas and they are used to compose
`schemas/src/gitlabform.json`. Each individual schemas typically correspond to variuos sections of
GitLabForm's configuration. Having individual schemas makes it easy to unit test them with different
sample data as well as easier to maintain.

Currently the goal of these schemas is to help users compose their GitLabForm configuration. The schemas
will be available via [schemastore catalog](https://www.schemastore.org/json/), which is supported by various
editors. Using these schemas, the editors can provide helpful hint/tooltip, auto completion, details/example of
configuration, etc.

## Required tools

- Python 3 and Pip 3 for development

## Environment setup

1. Create virtualenv with Python 3, for example in `venv` dir which is in `.gitignore` and activate it:

```
python3 -m venv venv
. venv/bin/activate
```

## Developing schemas

Curently the schemas are handwritten. They are not auto generated. Follow the existing schemas pattern when
developing a new schema. Following resources maybe helpful:

- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/): A good reference for JSON Schema.
- [python-jsonschema](https://python-jsonschema.readthedocs.io/en/stable/): The library used in unit test for validating schemas.
- [referencing](https://referencing.readthedocs.io/en/stable/): The library used in unit test that provides reference resolution between multiple schemas.

### Running unit tests locally

To run unit tests locally:

1. Activate the virtualenv created above

2. Install the dependencies for tests:

    ```
    pip install -e '.[test]'
    ```

3. Run `pytest schemas/tests` to run all the unit tests.
