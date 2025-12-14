"""
Alternative approach for configuration control using special key prefixes.

This module provides an alternative to YAML tags using special keys with underscores.
This approach doesn't require custom YAML parsing and works with standard YAML 1.1/1.2.

Special keys:
- _inherit: Control configuration inheritance (values: true, false, never, always, force)
- _enforce: Enforce configuration settings (value: true/false)
- _delete: Mark items for deletion (value: true/false or item name)
- _keep_existing: Keep existing values when merging (value: true/false)

Example:
    project_settings:
      _inherit: force
      topics:
        _keep_existing: true
        - topicA
        - topicB
"""

from typing import Any, Dict
from ruamel.yaml.comments import CommentedMap


def extract_special_keys(config: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract special control keys from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (control_keys, remaining_config)
    """
    if not isinstance(config, dict):
        return {}, config
    
    control_keys = {}
    remaining = {}
    
    for key, value in config.items():
        if key.startswith('_') and key[1:] in ['inherit', 'enforce', 'delete', 'keep_existing']:
            control_key = key[1:]  # Remove leading underscore
            control_keys[control_key] = value
        else:
            remaining[key] = value
    
    return control_keys, remaining


def process_special_keys(config: Any) -> Any:
    """
    Recursively process special keys in configuration.
    
    This converts special key prefixes into metadata that can be used
    by the configuration processing logic.
    
    Args:
        config: Configuration to process (dict, list, or other)
        
    Returns:
        Processed configuration with special keys extracted
    """
    if isinstance(config, dict):
        control_keys, remaining = extract_special_keys(config)
        
        # Recursively process nested structures
        processed = {}
        for key, value in remaining.items():
            processed[key] = process_special_keys(value)
        
        # If we found control keys, attach them as metadata
        if control_keys:
            # Store control keys in a special attribute if possible
            if isinstance(processed, CommentedMap):
                if not hasattr(processed, '_control_keys'):
                    processed._control_keys = {}
                processed._control_keys.update(control_keys)
        
        return processed
    
    elif isinstance(config, list):
        # Process each item in the list
        return [process_special_keys(item) for item in config]
    
    else:
        # Return scalar values as-is
        return config


def has_control_key(obj: Any, key: str) -> bool:
    """
    Check if an object has a control key.
    
    Args:
        obj: Object to check
        key: Control key name (without underscore)
        
    Returns:
        True if the control key exists
    """
    return hasattr(obj, '_control_keys') and key in obj._control_keys


def get_control_key(obj: Any, key: str, default=None) -> Any:
    """
    Get a control key value from an object.
    
    Args:
        obj: Object to get control key from
        key: Control key name (without underscore)
        default: Default value if key not found
        
    Returns:
        Control key value or default
    """
    if has_control_key(obj, key):
        return obj._control_keys[key]
    return default


def normalize_special_key_syntax(config_string: str) -> str:
    """
    Normalize special key syntax in configuration string.
    
    This is a utility function to help convert different syntax variations
    to a standardized form.
    
    Args:
        config_string: YAML configuration as string
        
    Returns:
        Normalized configuration string
    """
    # This is a placeholder for potential future enhancements
    # to normalize different syntax variations
    return config_string
