import json


def to_str(a_dict: dict) -> str:
    # arguably the most readable form of a dict in a single line
    # is JSON with sorted keys
    return json.dumps(a_dict, sort_keys=True)
