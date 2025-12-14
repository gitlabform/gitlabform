"""
Enhanced parser for GitLabForm configuration v5 with tag/special key support.

This parser extends the existing configuration parsing to handle:
- YAML custom tags (!inherit, !enforce, !delete, !keep_existing, !include)
- Special key prefixes (_inherit, _enforce, _delete, _keep_existing)

It provides an intermediate format with methods to query control directives
without polluting the actual configuration data.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap

from gitlabform.configuration.yaml_tags import (
    GitLabFormTagOrderedDict,
    GitLabFormTagScalar,
    GitLabFormTagList,
    InheritEnum,
    register_custom_tags,
)
from gitlabform.configuration.special_keys import (
    extract_special_keys,
    has_control_key,
    get_control_key,
)


class InheritanceMode(str, Enum):
    """Inheritance control modes."""
    TRUE = "true"
    FALSE = "false"
    NEVER = "never"
    ALWAYS = "always"
    FORCE = "force"


@dataclass
class ConfigNode:
    """
    Intermediate representation of a configuration node.
    
    This wraps the actual configuration data with metadata about
    control directives (inherit, enforce, delete, keep_existing).
    """
    
    # The actual configuration value (dict, list, scalar, etc.)
    value: Any
    
    # Control directive metadata
    inherit: Optional[str] = None
    enforce: bool = False
    delete: bool = False
    keep_existing: bool = False
    
    # Path to this node in the configuration tree
    path: str = ""
    
    # Child nodes (for mappings and sequences)
    children: Dict[str, 'ConfigNode'] = field(default_factory=dict)
    
    def is_enforced(self) -> bool:
        """Check if this node has enforcement enabled."""
        return self.enforce
    
    def get_inheritance(self) -> Optional[str]:
        """
        Get the inheritance mode for this node.
        
        Returns:
            One of: 'true', 'false', 'never', 'always', 'force', or None
        """
        return self.inherit
    
    def should_delete(self) -> bool:
        """Check if this node should be deleted."""
        return self.delete
    
    def should_keep_existing(self) -> bool:
        """Check if existing values should be kept when merging."""
        return self.keep_existing
    
    def has_control_directive(self) -> bool:
        """Check if this node has any control directives."""
        return (
            self.inherit is not None
            or self.enforce
            or self.delete
            or self.keep_existing
        )
    
    def get_value(self) -> Any:
        """Get the actual configuration value without metadata."""
        return self.value
    
    def get_child(self, key: str) -> Optional['ConfigNode']:
        """Get a child node by key."""
        return self.children.get(key)
    
    def has_child(self, key: str) -> bool:
        """Check if a child node exists."""
        return key in self.children
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary representation including metadata.
        
        Returns:
            Dictionary with 'value', 'metadata', and optionally 'children'
        """
        result = {
            'value': self.value,
            'metadata': {
                'inherit': self.inherit,
                'enforce': self.enforce,
                'delete': self.delete,
                'keep_existing': self.keep_existing,
            },
            'path': self.path,
        }
        
        if self.children:
            result['children'] = {
                key: child.to_dict()
                for key, child in self.children.items()
            }
        
        return result


class ConfigV5Parser:
    """
    Parser for GitLabForm configuration v5.
    
    This parser handles both YAML tags and special key prefixes,
    creating an intermediate representation that separates
    configuration data from control directives.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.yaml = ruamel.yaml.YAML()
        register_custom_tags(self.yaml)
    
    def parse(self, config_string: str) -> ConfigNode:
        """
        Parse a configuration string into a ConfigNode tree.
        
        Args:
            config_string: YAML configuration as string
            
        Returns:
            Root ConfigNode representing the entire configuration
        """
        # Parse YAML with custom tags
        raw_config = self.yaml.load(config_string)
        
        # Convert to ConfigNode tree
        root = self._convert_to_node(raw_config, path="root")
        
        return root
    
    def parse_file(self, file_path: str) -> ConfigNode:
        """
        Parse a configuration file into a ConfigNode tree.
        
        Args:
            file_path: Path to YAML configuration file
            
        Returns:
            Root ConfigNode representing the entire configuration
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.parse(f.read())
    
    def _convert_to_node(
        self,
        value: Any,
        path: str = "",
        parent_directives: Optional[Dict[str, Any]] = None
    ) -> ConfigNode:
        """
        Convert a parsed YAML value to a ConfigNode.
        
        Args:
            value: Parsed YAML value (may have tags or special keys)
            path: Current path in configuration tree
            parent_directives: Inherited control directives from parent
            
        Returns:
            ConfigNode with extracted metadata
        """
        parent_directives = parent_directives or {}
        
        # Extract control directives from this node
        directives = self._extract_directives(value)
        
        # Merge with parent directives (child overrides parent)
        merged_directives = {**parent_directives, **directives}
        
        # Create the node
        node = ConfigNode(
            value=self._get_clean_value(value),
            path=path,
            inherit=merged_directives.get('inherit'),
            enforce=merged_directives.get('enforce', False),
            delete=merged_directives.get('delete', False),
            keep_existing=merged_directives.get('keep_existing', False),
        )
        
        # Recursively process children
        if isinstance(value, dict):
            # Process mapping children
            clean_dict = self._get_clean_dict(value)
            for key, child_value in clean_dict.items():
                child_path = f"{path}.{key}" if path else key
                child_node = self._convert_to_node(
                    child_value,
                    path=child_path,
                    parent_directives=merged_directives
                )
                node.children[key] = child_node
        
        elif isinstance(value, (list, GitLabFormTagList)):
            # Process sequence children
            clean_list = self._get_clean_list(value)
            for idx, child_value in enumerate(clean_list):
                child_path = f"{path}[{idx}]"
                child_node = self._convert_to_node(
                    child_value,
                    path=child_path,
                    parent_directives=merged_directives
                )
                node.children[str(idx)] = child_node
        
        return node
    
    def _extract_directives(self, value: Any) -> Dict[str, Any]:
        """
        Extract control directives from a value.
        
        Handles both YAML tags and special keys.
        
        Args:
            value: Value to extract directives from
            
        Returns:
            Dictionary of control directives
        """
        directives = {}
        directive_names = ['inherit', 'enforce', 'delete', 'keep_existing']
        
        # Check for YAML tag directives
        if hasattr(value, 'get_tag'):
            for name in directive_names:
                if value.has_tag(name):
                    directives[name] = value.get_tag(name)
        
        # Check for special key directives
        if isinstance(value, dict):
            control_keys, _ = extract_special_keys(value)
            directives.update(control_keys)
        
        # Check for control keys on object
        for name in directive_names:
            if has_control_key(value, name):
                directives[name] = get_control_key(value, name)
        
        return directives
    
    def _get_clean_value(self, value: Any) -> Any:
        """
        Get the value without any control directives.
        
        Args:
            value: Raw value (may have tags or special keys)
            
        Returns:
            Clean value without control metadata
        """
        # Handle tagged scalar
        if isinstance(value, GitLabFormTagScalar):
            return value.value
        
        # Handle tagged dict
        if isinstance(value, GitLabFormTagOrderedDict):
            return dict(value)
        
        # Handle tagged list
        if isinstance(value, GitLabFormTagList):
            return list(value)
        
        # Handle dict with special keys
        if isinstance(value, dict):
            _, clean_dict = extract_special_keys(value)
            return clean_dict
        
        return value
    
    def _get_clean_dict(self, value: Any) -> Dict[str, Any]:
        """Get dictionary without special keys."""
        if isinstance(value, (GitLabFormTagOrderedDict, dict)):
            _, clean_dict = extract_special_keys(dict(value))
            return clean_dict
        return {}
    
    def _get_clean_list(self, value: Any) -> List[Any]:
        """Get list items."""
        if isinstance(value, (GitLabFormTagList, list)):
            return list(value)
        return []


def parse_config_v5(config_string: str) -> ConfigNode:
    """
    Convenience function to parse a v5 configuration string.
    
    Args:
        config_string: YAML configuration as string
        
    Returns:
        Root ConfigNode representing the configuration
        
    Example:
        >>> config = '''
        ... projects_and_groups:
        ...   group1/*:
        ...     project_settings: !inherit force
        ...     topics: !keep_existing
        ...       - !delete oldTopic
        ...       - newTopic
        ... '''
        >>> root = parse_config_v5(config)
        >>> group_node = root.get_child('projects_and_groups').get_child('group1/*')
        >>> settings_node = group_node.get_child('project_settings')
        >>> settings_node.get_inheritance()
        'force'
        >>> topics_node = group_node.get_child('topics')
        >>> topics_node.should_keep_existing()
        True
    """
    parser = ConfigV5Parser()
    return parser.parse(config_string)


def parse_config_v5_file(file_path: str) -> ConfigNode:
    """
    Convenience function to parse a v5 configuration file.
    
    Args:
        file_path: Path to YAML configuration file
        
    Returns:
        Root ConfigNode representing the configuration
    """
    parser = ConfigV5Parser()
    return parser.parse_file(file_path)
