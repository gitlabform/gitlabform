"""
Custom YAML tags support for GitLabForm configuration v5.

This module provides custom YAML tag constructors for:
- !inherit: Control configuration inheritance (values: true, false, never, always, force)
- !enforce: Enforce configuration settings
- !delete: Mark items for deletion
- !keep_existing: Keep existing values when merging
- !include: Include external YAML files

These tags can be used anywhere in the configuration without cluttering the JSON Schema.
"""

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Union
from collections import OrderedDict

import ruamel.yaml
from ruamel.yaml.constructor import Constructor
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode


# Enum for inherit values
class InheritEnum(str, Enum):
    """Valid values for the !inherit tag."""

    TRUE = "true"
    FALSE = "false"
    NEVER = "never"
    ALWAYS = "always"
    FORCE = "force"


# Custom Ordered Dict to store tags
class GitLabFormTagOrderedDict(OrderedDict):
    """A custom ordered dictionary that tracks parsed YAML tags."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tags: Dict[str, Any] = {}

    def set_tag(self, key: str, tag: Any) -> None:
        """Associate a custom tag with a key."""
        self._tags[key] = tag

    def get_tags(self) -> Dict[str, Any]:
        """Retrieve all stored tags."""
        return self._tags

    def has_tag(self, key: str) -> bool:
        """Check if a tag exists."""
        return key in self._tags

    def get_tag(self, key: str, default=None) -> Any:
        """Get a specific tag value."""
        return self._tags.get(key, default)


# Custom Scalar to store tags
@dataclass
class GitLabFormTagScalar:
    """A wrapper for scalar values that store tags."""

    value: Any
    tags: Dict[str, Any] = field(default_factory=dict)

    def has_tag(self, key: str) -> bool:
        """Check if a tag exists."""
        return key in self.tags

    def get_tag(self, key: str, default=None) -> Any:
        """Get a specific tag value."""
        return self.tags.get(key, default)


# Custom List to store tags
class GitLabFormTagList(list):
    """A custom list that tracks parsed YAML tags."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tags: Dict[str, Any] = {}

    def set_tag(self, key: str, tag: Any) -> None:
        """Associate a custom tag with the list."""
        self._tags[key] = tag

    def get_tags(self) -> Dict[str, Any]:
        """Retrieve all stored tags."""
        return self._tags

    def has_tag(self, key: str) -> bool:
        """Check if a tag exists."""
        return key in self._tags

    def get_tag(self, key: str, default=None) -> Any:
        """Get a specific tag value."""
        return self._tags.get(key, default)


# Constructor for !enforce
def enforce_constructor(loader: Constructor, node: MappingNode) -> GitLabFormTagOrderedDict:
    """
    Constructor for !enforce tag.

    Usage:
        project_settings:
          !enforce
          topics:
            - topicA
    """
    result = GitLabFormTagOrderedDict()
    result.set_tag("enforce", True)

    for key_node, value_node in node.value:
        key: str = key_node.value
        value: Any = loader.construct_object(value_node)
        result[key] = value

    return result


# Constructor for !delete
def delete_constructor(loader: Constructor, node: ScalarNode) -> GitLabFormTagScalar:
    """
    Constructor for !delete tag.

    Usage:
        - !delete topicA
    """
    value: str = loader.construct_scalar(node)
    return GitLabFormTagScalar(value, {"delete": True})


# Constructor for !inherit
def inherit_constructor(
    loader: Constructor,
    node: Union[MappingNode, SequenceNode, ScalarNode],
) -> Any:
    """
    Constructor for !inherit tag.

    Usage:
        project_settings: !inherit force
        topics: !inherit [never, keep_existing]
    """
    if isinstance(node, SequenceNode):
        values: List[Any] = loader.construct_sequence(node, deep=True)
        main_value: Any = values[0] if values else None
        additional_tags: List[Any] = values[1:]

        if main_value in {e.value for e in InheritEnum}:
            result = GitLabFormTagList(values[1:])
            result.set_tag("inherit", main_value)

            for extra in additional_tags:
                if extra == "keep_existing":
                    result.set_tag("keep_existing", True)
                else:
                    raise ValueError(f"Invalid combination of tags with inherit: {extra}")

            return result
        else:
            raise ValueError(f"Invalid inherit value: {main_value}")



    else:  # ScalarNode
        value: str = loader.construct_scalar(node)
        if value in {e.value for e in InheritEnum}:
            result = GitLabFormTagOrderedDict()
            result.set_tag("inherit", value)
            return result
        else:
            raise ValueError(f"Invalid inherit value: {value}")


# Constructor for !keep_existing
def keep_existing_constructor(loader: Constructor, node: Union[ScalarNode, SequenceNode]) -> Any:
    """
    Constructor for !keep_existing tag.

    Usage:
        topics: !keep_existing
        - topicA
        - topicB
    """
    if isinstance(node, SequenceNode):
        result = GitLabFormTagList(loader.construct_sequence(node, deep=True))
        result.set_tag("keep_existing", True)
        return result
    else:
        # For scalar or other nodes, just mark them
        value: Any = loader.construct_scalar(node) if isinstance(node, ScalarNode) else loader.construct_object(node)
        return GitLabFormTagScalar(value, {"keep_existing": True})


# Constructor for !include
def include_constructor(loader: Constructor, node: ScalarNode) -> Any:
    """
    Constructor for !include tag.

    Usage:
        !include path/to/file.yml
    """
    file_path_str = loader.construct_scalar(node)
    file_path = pathlib.Path(file_path_str)

    # If the path is not absolute, treat it as relative to the current working directory.
    # In a future enhancement, this could be made relative to the including config file's directory
    # by passing the config directory context through the loader.
    if not file_path.is_absolute():
        file_path = pathlib.Path.cwd() / file_path

    if not file_path.exists():
        raise IOError(f"Included external YAML file '{file_path}' does not exist.")

    yaml = ruamel.yaml.YAML()
    # Register the same constructors for the included file
    register_custom_tags(yaml)

    with file_path.open("r", encoding="utf-8") as f:
        return yaml.load(f)


def register_custom_tags(yaml_instance: ruamel.yaml.YAML) -> None:
    """
    Register all custom YAML tags with a YAML instance.

    Args:
        yaml_instance: The ruamel.yaml.YAML instance to register tags with
    """
    yaml_instance.constructor.add_constructor("!enforce", enforce_constructor)
    yaml_instance.constructor.add_constructor("!delete", delete_constructor)
    yaml_instance.constructor.add_constructor("!inherit", inherit_constructor)
    yaml_instance.constructor.add_constructor("!keep_existing", keep_existing_constructor)
    yaml_instance.constructor.add_constructor("!include", include_constructor)
