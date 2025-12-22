"""
Unit tests for special key prefixes approach in GitLabForm configuration v5.
"""

import logging
import pytest

from gitlabform.configuration.special_keys import (
    extract_special_keys,
    process_special_keys,
    has_control_key,
    get_control_key,
)

logger = logging.getLogger(__name__)


class TestExtractSpecialKeys:
    """Tests for extracting special keys from configuration."""

    def test_extract_inherit_key(self):
        """Test extracting _inherit key."""
        config = {
            "_inherit": "force",
            "visibility": "internal",
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {"inherit": "force"}
        assert remaining == {"visibility": "internal"}

    def test_extract_multiple_special_keys(self):
        """Test extracting multiple special keys."""
        config = {
            "_inherit": "force",
            "_enforce": True,
            "visibility": "internal",
            "topics": ["topicA"],
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {"inherit": "force", "enforce": True}
        assert remaining == {"visibility": "internal", "topics": ["topicA"]}

    def test_extract_keep_existing_key(self):
        """Test extracting _keep_existing key."""
        config = {
            "_keep_existing": True,
            "items": ["item1", "item2"],
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {"keep_existing": True}
        assert remaining == {"items": ["item1", "item2"]}

    def test_extract_delete_key(self):
        """Test extracting _delete key."""
        config = {
            "_delete": True,
            "name": "topicA",
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {"delete": True}
        assert remaining == {"name": "topicA"}

    def test_no_special_keys(self):
        """Test config with no special keys."""
        config = {
            "visibility": "internal",
            "topics": ["topicA"],
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {}
        assert remaining == config

    def test_underscore_but_not_special(self):
        """Test keys with underscore that aren't special keys."""
        config = {
            "_custom": "value",
            "_other": "data",
            "visibility": "internal",
        }
        control, remaining = extract_special_keys(config)
        
        assert control == {}
        assert remaining == config

    def test_non_dict_input(self):
        """Test with non-dict input."""
        control, remaining = extract_special_keys("not a dict")
        
        assert control == {}
        assert remaining == "not a dict"


class TestProcessSpecialKeys:
    """Tests for processing special keys recursively."""

    def test_process_simple_dict(self):
        """Test processing simple dictionary."""
        config = {
            "_inherit": "force",
            "visibility": "internal",
        }
        processed = process_special_keys(config)
        
        assert "visibility" in processed
        assert "_inherit" not in processed

    def test_process_nested_dict(self):
        """Test processing nested dictionary."""
        config = {
            "project_settings": {
                "_inherit": "force",
                "visibility": "internal",
                "topics": {
                    "_keep_existing": True,
                    "items": ["topicA"],
                }
            }
        }
        processed = process_special_keys(config)
        
        assert "project_settings" in processed
        assert "visibility" in processed["project_settings"]
        assert "_inherit" not in processed["project_settings"]
        assert "topics" in processed["project_settings"]
        assert "_keep_existing" not in processed["project_settings"]["topics"]

    def test_process_list(self):
        """Test processing list."""
        config = [
            {"_delete": True, "name": "topicA"},
            {"name": "topicB"},
        ]
        processed = process_special_keys(config)
        
        assert len(processed) == 2
        assert "name" in processed[0]
        assert "_delete" not in processed[0]

    def test_process_mixed_structure(self):
        """Test processing mixed nested structure."""
        config = {
            "groups": {
                "group1": {
                    "_inherit": "always",
                    "members": [
                        {"_delete": True, "name": "user1"},
                        {"name": "user2"},
                    ]
                }
            }
        }
        processed = process_special_keys(config)
        
        assert "groups" in processed
        assert "group1" in processed["groups"]
        assert "_inherit" not in processed["groups"]["group1"]
        assert "members" in processed["groups"]["group1"]


class TestControlKeyHelpers:
    """Tests for control key helper functions."""

    def test_has_control_key_true(self):
        """Test has_control_key when key exists."""
        obj = type('obj', (object,), {})()
        obj._control_keys = {"inherit": "force"}
        
        assert has_control_key(obj, "inherit") is True

    def test_has_control_key_false(self):
        """Test has_control_key when key doesn't exist."""
        obj = type('obj', (object,), {})()
        obj._control_keys = {"inherit": "force"}
        
        assert has_control_key(obj, "enforce") is False

    def test_has_control_key_no_attr(self):
        """Test has_control_key when object has no _control_keys."""
        obj = type('obj', (object,), {})()
        
        assert has_control_key(obj, "inherit") is False

    def test_get_control_key_exists(self):
        """Test get_control_key when key exists."""
        obj = type('obj', (object,), {})()
        obj._control_keys = {"inherit": "force"}
        
        assert get_control_key(obj, "inherit") == "force"

    def test_get_control_key_missing_with_default(self):
        """Test get_control_key with default for missing key."""
        obj = type('obj', (object,), {})()
        obj._control_keys = {"inherit": "force"}
        
        assert get_control_key(obj, "enforce", "default") == "default"

    def test_get_control_key_missing_no_default(self):
        """Test get_control_key without default for missing key."""
        obj = type('obj', (object,), {})()
        obj._control_keys = {"inherit": "force"}
        
        assert get_control_key(obj, "enforce") is None


class TestComparisonWithTags:
    """Tests comparing special keys with YAML tags approach."""

    def test_equivalent_functionality(self):
        """Test that special keys provide equivalent functionality to tags."""
        # Special keys version
        special_keys_config = {
            "project_settings": {
                "_inherit": "force",
                "visibility": "internal",
            }
        }
        
        control, remaining = extract_special_keys(special_keys_config["project_settings"])
        
        # Should extract the same control information
        assert control["inherit"] == "force"
        assert remaining["visibility"] == "internal"

    def test_nested_equivalent(self):
        """Test nested structures are equivalent."""
        config = {
            "groups": {
                "group1": {
                    "_inherit": "force",
                    "topics": {
                        "_keep_existing": True,
                        "items": ["topicA", "topicB"]
                    }
                }
            }
        }
        
        processed = process_special_keys(config)
        
        # Verify structure is preserved minus control keys
        assert "groups" in processed
        assert "group1" in processed["groups"]
        assert "topics" in processed["groups"]["group1"]
        assert "items" in processed["groups"]["group1"]["topics"]
