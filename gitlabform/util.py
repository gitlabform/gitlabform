import json
from datetime import date
from io import StringIO

from ruamel.yaml import YAML


def format_expires_at(expires_at):
    if isinstance(expires_at, date):
        return expires_at.strftime("%Y-%m-%d")
    return expires_at


def to_str(a_dict: dict) -> str:
    # arguably the most readable form of a dict in a single line
    # is JSON with sorted keys
    return json.dumps(a_dict, sort_keys=True, default=str)


def yaml_config_to_string(yaml) -> str:
    """
    Provides a convenience wrapper around ruamel.yaml to output to a string
    ez_yaml used to perform this task but in v2.2 they seem to have over complicated the implementation and it is
    breaking in ruamel.yaml when parsing the yaml, with no way for us to configure it.
    We can provide a simple native implementation around ruamel.yaml to configure it consistently.
    :param yaml:
    :return:
    """
    yaml_loader = configure_ruamel_yaml_loader()

    # dump to StringIO
    string_stream = StringIO()
    yaml_loader.dump(yaml, string_stream)
    config_yaml_string = string_stream.getvalue()
    string_stream.close()

    return config_yaml_string


def configure_ruamel_yaml_loader(typ=None, pure=False, output=None, plug_ins=None) -> YAML:
    """
    Takes inputs matching ruamel.yaml __init__ and configures with indentation, duplicate key allowance and null representor
    :return: instance of ruamel.yaml
    """
    yaml_loader = YAML(typ=typ, pure=pure, output=output, plug_ins=plug_ins)
    yaml_loader.indent(mapping=3, sequence=2, offset=0)
    yaml_loader.allow_duplicate_keys = True
    yaml_loader.explicit_start = False
    # show null
    yaml_loader.representer.add_representer(
        type(None),
        lambda self, data: self.represent_scalar("tag:yaml.org,2002:null", "null"),
    )
    return yaml_loader
