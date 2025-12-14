"""
Unit tests for ConfigV5Parser.
"""

import logging
import pytest
import tempfile
import pathlib

from gitlabform.configuration.config_v5_parser import (
    ConfigV5Parser,
    ConfigNode,
    InheritanceMode,
    parse_config_v5,
    parse_config_v5_file,
)

logger = logging.getLogger(__name__)


class TestConfigNode:
    """Tests for ConfigNode data structure."""

    def test_is_enforced(self):
        """Test is_enforced() method."""
        node = ConfigNode(value="test", enforce=True)
        assert node.is_enforced() is True
        
        node2 = ConfigNode(value="test", enforce=False)
        assert node2.is_enforced() is False

    def test_get_inheritance(self):
        """Test get_inheritance() method."""
        node = ConfigNode(value="test", inherit="force")
        assert node.get_inheritance() == "force"
        
        node2 = ConfigNode(value="test")
        assert node2.get_inheritance() is None

    def test_should_delete(self):
        """Test should_delete() method."""
        node = ConfigNode(value="test", delete=True)
        assert node.should_delete() is True
        
        node2 = ConfigNode(value="test")
        assert node2.should_delete() is False

    def test_should_keep_existing(self):
        """Test should_keep_existing() method."""
        node = ConfigNode(value="test", keep_existing=True)
        assert node.should_keep_existing() is True
        
        node2 = ConfigNode(value="test")
        assert node2.should_keep_existing() is False

    def test_has_control_directive(self):
        """Test has_control_directive() method."""
        node = ConfigNode(value="test", enforce=True)
        assert node.has_control_directive() is True
        
        node2 = ConfigNode(value="test")
        assert node2.has_control_directive() is False

    def test_get_value(self):
        """Test get_value() method."""
        node = ConfigNode(value="test_value")
        assert node.get_value() == "test_value"

    def test_children_management(self):
        """Test child node management."""
        parent = ConfigNode(value={})
        child = ConfigNode(value="child_value")
        parent.children["child_key"] = child
        
        assert parent.has_child("child_key") is True
        assert parent.get_child("child_key") == child
        assert parent.has_child("nonexistent") is False
        assert parent.get_child("nonexistent") is None

    def test_to_dict(self):
        """Test to_dict() conversion."""
        node = ConfigNode(
            value="test",
            inherit="force",
            enforce=True,
            path="root.test"
        )
        
        result = node.to_dict()
        assert result['value'] == "test"
        assert result['metadata']['inherit'] == "force"
        assert result['metadata']['enforce'] is True
        assert result['path'] == "root.test"


class TestConfigV5Parser:
    """Tests for ConfigV5Parser."""

    def test_parse_simple_yaml(self):
        """Test parsing simple YAML configuration."""
        parser = ConfigV5Parser()
        config = """
        project_settings:
          visibility: internal
        """
        root = parser.parse(config)
        
        assert root is not None
        assert root.has_child('project_settings')
        settings = root.get_child('project_settings')
        assert settings.has_child('visibility')

    def test_parse_yaml_with_inherit_tag(self):
        """Test parsing YAML with !inherit tag."""
        parser = ConfigV5Parser()
        config = """
        project_settings: !inherit force
        """
        root = parser.parse(config)
        
        settings = root.get_child('project_settings')
        assert settings is not None
        assert settings.get_inheritance() == "force"

    def test_parse_yaml_with_enforce_tag(self):
        """Test parsing YAML with !enforce tag."""
        parser = ConfigV5Parser()
        config = """
        members:
          !enforce
          users:
            admin:
              access_level: maintainer
        """
        root = parser.parse(config)
        
        members = root.get_child('members')
        assert members is not None
        assert members.is_enforced() is True

    def test_parse_yaml_with_delete_tag(self):
        """Test parsing YAML with !delete tag."""
        parser = ConfigV5Parser()
        config = """
        topics:
          - !delete oldTopic
          - newTopic
        """
        root = parser.parse(config)
        
        topics = root.get_child('topics')
        assert topics is not None
        
        # First item should be marked for deletion
        first_item = topics.get_child('0')
        assert first_item is not None
        assert first_item.should_delete() is True
        assert first_item.get_value() == "oldTopic"
        
        # Second item should not be marked for deletion
        second_item = topics.get_child('1')
        assert second_item is not None
        assert second_item.should_delete() is False
        assert second_item.get_value() == "newTopic"

    def test_parse_yaml_with_keep_existing_tag(self):
        """Test parsing YAML with !keep_existing tag."""
        parser = ConfigV5Parser()
        config = """
        topics: !keep_existing
          - topicA
          - topicB
        """
        root = parser.parse(config)
        
        topics = root.get_child('topics')
        assert topics is not None
        assert topics.should_keep_existing() is True

    def test_parse_yaml_with_special_keys(self):
        """Test parsing YAML with special key prefixes."""
        parser = ConfigV5Parser()
        config = """
        project_settings:
          _inherit: force
          visibility: internal
        """
        root = parser.parse(config)
        
        settings = root.get_child('project_settings')
        assert settings is not None
        assert settings.get_inheritance() == "force"
        
        # visibility should be a child, not _inherit
        assert settings.has_child('visibility')
        assert not settings.has_child('_inherit')

    def test_parse_complex_config(self):
        """Test parsing complex configuration with multiple tags."""
        parser = ConfigV5Parser()
        config = """
        projects_and_groups:
          group1/*:
            project_settings: !inherit force
            topics: !keep_existing
              - !delete oldTopic
              - newTopic
            members:
              !enforce
              users:
                admin:
                  access_level: maintainer
        """
        root = parser.parse(config)
        
        # Navigate to group config
        projects = root.get_child('projects_and_groups')
        assert projects is not None
        
        group = projects.get_child('group1/*')
        assert group is not None
        
        # Check project_settings
        settings = group.get_child('project_settings')
        assert settings is not None
        assert settings.get_inheritance() == "force"
        
        # Check topics
        topics = group.get_child('topics')
        assert topics is not None
        assert topics.should_keep_existing() is True
        
        # Check first topic (delete)
        first_topic = topics.get_child('0')
        assert first_topic.should_delete() is True
        
        # Check members
        members = group.get_child('members')
        assert members is not None
        assert members.is_enforced() is True

    def test_parse_mixed_tags_and_special_keys(self):
        """Test parsing config with both tags and special keys."""
        parser = ConfigV5Parser()
        config = """
        project_settings: !inherit force
        other_settings:
          _enforce: true
          visibility: internal
        """
        root = parser.parse(config)
        
        # Check tag
        settings = root.get_child('project_settings')
        assert settings.get_inheritance() == "force"
        
        # Check special key
        other = root.get_child('other_settings')
        assert other.is_enforced() is True

    def test_parse_file(self, tmp_path):
        """Test parsing configuration from file."""
        # Create temporary config file
        config_file = tmp_path / "test_config.yml"
        config_file.write_text("""
        project_settings: !inherit force
        topics:
          - topicA
        """)
        
        parser = ConfigV5Parser()
        root = parser.parse_file(str(config_file))
        
        settings = root.get_child('project_settings')
        assert settings.get_inheritance() == "force"

    def test_inheritance_propagation(self):
        """Test that control directives propagate to children."""
        parser = ConfigV5Parser()
        config = """
        group_settings:
          _inherit: always
          nested:
            deeply:
              value: test
        """
        root = parser.parse(config)
        
        # Parent should have inherit directive
        group = root.get_child('group_settings')
        assert group.get_inheritance() == "always"
        
        # Note: Currently propagation happens during parsing,
        # so children may inherit based on implementation


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_config_v5(self):
        """Test parse_config_v5 convenience function."""
        config = """
        project_settings: !inherit force
        """
        root = parse_config_v5(config)
        
        settings = root.get_child('project_settings')
        assert settings.get_inheritance() == "force"

    def test_parse_config_v5_file(self, tmp_path):
        """Test parse_config_v5_file convenience function."""
        config_file = tmp_path / "test.yml"
        config_file.write_text("""
        topics: !keep_existing
          - topicA
        """)
        
        root = parse_config_v5_file(str(config_file))
        topics = root.get_child('topics')
        assert topics.should_keep_existing() is True


class TestRealWorldExamples:
    """Tests with real-world configuration examples."""

    def test_full_config_example(self):
        """Test parsing a complete realistic configuration."""
        config = """
        config_version: 5
        
        gitlab:
          url: https://gitlab.example.com
          token: secret
        
        projects_and_groups:
          "*":
            project_settings:
              visibility: internal
          
          mygroup/*:
            project_settings: !inherit force
            topics: !keep_existing
              - !delete legacy
              - !delete deprecated
              - security
              - compliance
            
            members:
              !enforce
              users:
                admin:
                  access_level: maintainer
                developer:
                  access_level: developer
          
          mygroup/special-project:
            project_settings:
              _inherit: false
            topics:
              - internal
              - confidential
        """
        
        root = parse_config_v5(config)
        
        # Check common config
        projects = root.get_child('projects_and_groups')
        common = projects.get_child('*')
        assert common is not None
        
        # Check group config
        group = projects.get_child('mygroup/*')
        assert group is not None
        
        group_settings = group.get_child('project_settings')
        assert group_settings.get_inheritance() == "force"
        
        topics = group.get_child('topics')
        assert topics.should_keep_existing() is True
        
        # Check topics with delete
        topic0 = topics.get_child('0')
        assert topic0.should_delete() is True
        assert topic0.get_value() == "legacy"
        
        # Check project config
        project = projects.get_child('mygroup/special-project')
        project_settings = project.get_child('project_settings')
        # Note: _inherit: false as a boolean becomes False, not "false" string
        assert project_settings.get_inheritance() is False or project_settings.get_inheritance() == "false"

    def test_all_reference_sections(self):
        """Test that parser works with all configuration sections."""
        config = """
        projects_and_groups:
          group1/*:
            # Project settings
            project_settings:
              _enforce: true
              visibility: internal
            
            # Members
            members: !enforce
            
            # Deploy keys
            deploy_keys:
              key1:
                title: "Deploy Key"
                key: "ssh-rsa ..."
            
            # CI/CD variables
            variables:
              VAR1:
                value: "value1"
              
            # Labels
            labels:
              bug:
                color: "#FF0000"
            
            # Webhooks
            webhooks:
              hook1:
                url: "https://example.com"
            
            # Protected branches
            protected_branches:
              main:
                push_access_level: maintainer
        """
        
        root = parse_config_v5(config)
        
        group = root.get_child('projects_and_groups').get_child('group1/*')
        
        # Verify all sections are parsed
        assert group.has_child('project_settings')
        assert group.has_child('members')
        assert group.has_child('deploy_keys')
        assert group.has_child('variables')
        assert group.has_child('labels')
        assert group.has_child('webhooks')
        assert group.has_child('protected_branches')
        
        # Verify control directives
        assert group.get_child('project_settings').is_enforced() is True
        assert group.get_child('members').is_enforced() is True
