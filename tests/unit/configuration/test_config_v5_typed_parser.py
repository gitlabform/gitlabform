"""
Unit tests for ConfigV5TypedParser.
"""

import logging
import pytest
import tempfile
import pathlib

from gitlabform.configuration.config_v5_typed_parser import (
    ConfigV5TypedParser,
    parse_typed_config_v5,
    parse_typed_config_v5_file,
)
from gitlabform.configuration.config_v5_objects import (
    EntityConfig,
    ProjectSettingsConfig,
    BadgesConfig,
    MembersConfig,
    PushRulesConfig,
    Visibility,
)

logger = logging.getLogger(__name__)


class TestConfigV5TypedParser:
    """Tests for ConfigV5TypedParser."""

    def test_parse_simple_config(self):
        """Test parsing simple configuration."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            project_settings:
              visibility: internal
        """
        entities = parser.parse(config)
        
        assert 'group1/*' in entities
        entity = entities['group1/*']
        assert isinstance(entity, EntityConfig)
        assert entity.project_settings is not None
        assert entity.project_settings.visibility == Visibility.INTERNAL

    def test_parse_with_inherit_tag(self):
        """Test parsing with !inherit tag."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            project_settings: !inherit force
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        assert entity.project_settings.get_inheritance() == "force"

    def test_parse_with_enforce_tag(self):
        """Test parsing with !enforce tag."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            badges:
              !enforce
              coverage:
                name: "Coverage"
                link_url: "http://example.com"
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        assert entity.badges is not None
        assert entity.badges.is_enforced() is True
        assert 'coverage' in entity.badges.badges

    def test_parse_project_settings(self):
        """Test parsing detailed project settings."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/project1:
            project_settings:
              default_branch: main
              visibility: internal
              topics:
                - security
                - compliance
              only_allow_merge_if_pipeline_succeeds: true
        """
        entities = parser.parse(config)
        
        entity = entities['group1/project1']
        settings = entity.project_settings
        assert settings.default_branch == "main"
        assert settings.visibility == Visibility.INTERNAL
        assert settings.topics == ["security", "compliance"]
        assert settings.only_allow_merge_if_pipeline_succeeds is True

    def test_parse_badges(self):
        """Test parsing badges configuration."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            badges:
              coverage:
                name: "Coverage"
                link_url: "http://example.com/coverage"
                image_url: "http://example.com/badge.svg"
              pipeline:
                name: "Pipeline"
                link_url: "http://example.com/pipeline"
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        badges = entity.badges
        assert len(badges.badges) == 2
        assert 'coverage' in badges.badges
        assert badges.badges['coverage'].name == "Coverage"
        assert badges.badges['pipeline'].name == "Pipeline"

    def test_parse_members(self):
        """Test parsing members configuration."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            members:
              !enforce
              users:
                user1:
                  access_level: maintainer
                user2:
                  access_level: developer
                  expires_at: "2025-12-31"
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        members = entity.members
        assert members.is_enforced() is True
        assert len(members.users) == 2
        assert 'user1' in members.users
        assert members.users['user1'].access_level == "maintainer"

    def test_parse_push_rules(self):
        """Test parsing push rules configuration."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            group_push_rules:
              commit_message_regex: '(.|\s)*\S(.|\s)*'
              member_check: false
              commit_committer_check: true
              max_file_size: 100
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        rules = entity.group_push_rules
        assert rules.commit_message_regex == '(.|\s)*\S(.|\s)*'
        assert rules.member_check is False
        assert rules.commit_committer_check is True
        assert rules.max_file_size == 100

    def test_parse_multiple_entities(self):
        """Test parsing multiple entities."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          "*":
            project_settings:
              visibility: internal
          group1/*:
            project_settings:
              visibility: private
          group1/project1:
            project_settings:
              visibility: public
        """
        entities = parser.parse(config)
        
        assert len(entities) == 3
        assert '*' in entities
        assert 'group1/*' in entities
        assert 'group1/project1' in entities
        
        assert entities['*'].project_settings.visibility == Visibility.INTERNAL
        assert entities['group1/*'].project_settings.visibility == Visibility.PRIVATE
        assert entities['group1/project1'].project_settings.visibility == Visibility.PUBLIC

    def test_get_configs_method(self):
        """Test EntityConfig.get_configs() method."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            project_settings:
              visibility: internal
            badges:
              coverage:
                name: "Coverage"
                link_url: "http://example.com"
            members:
              users:
                user1:
                  access_level: maintainer
        """
        entities = parser.parse(config)
        
        entity = entities['group1/*']
        configs = entity.get_configs()
        
        assert len(configs) == 3
        # Should contain project_settings, badges, and members
        config_types = [type(c).__name__ for c in configs]
        assert 'ProjectSettingsConfig' in config_types
        assert 'BadgesConfig' in config_types
        assert 'MembersConfig' in config_types

    def test_is_project_and_is_group(self):
        """Test is_project() and is_group() methods."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/*:
            project_settings:
              visibility: internal
          group1/project1:
            project_settings:
              visibility: private
        """
        entities = parser.parse(config)
        
        group_entity = entities['group1/*']
        project_entity = entities['group1/project1']
        
        assert group_entity.is_group() is True
        assert group_entity.is_project() is False
        
        assert project_entity.is_project() is True
        assert project_entity.is_group() is False

    def test_parse_file(self, tmp_path):
        """Test parsing from file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("""
        projects_and_groups:
          group1/*:
            project_settings: !inherit force
        """)
        
        parser = ConfigV5TypedParser()
        entities = parser.parse_file(str(config_file))
        
        entity = entities['group1/*']
        assert entity.project_settings.get_inheritance() == "force"

    def test_convenience_functions(self):
        """Test convenience functions."""
        config = """
        projects_and_groups:
          group1/*:
            project_settings: !inherit force
        """
        
        entities = parse_typed_config_v5(config)
        assert 'group1/*' in entities
        assert entities['group1/*'].project_settings.get_inheritance() == "force"

    def test_complex_real_world_config(self):
        """Test parsing complex real-world configuration."""
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
            badges:
              !enforce
              coverage:
                name: "Coverage"
                link_url: "http://example.com/coverage"
              pipeline:
                name: "Pipeline"
                link_url: "http://example.com/pipeline"
            
            members:
              !enforce
              users:
                admin:
                  access_level: maintainer
                developer:
                  access_level: developer
            
            group_push_rules:
              commit_message_regex: '(.|\s)*\S(.|\s)*'
              member_check: false
          
          mygroup/special-project:
            project_settings:
              visibility: private
              topics:
                - confidential
                - internal
        """
        
        entities = parse_typed_config_v5(config)
        
        # Check common config
        assert '*' in entities
        common = entities['*']
        assert common.project_settings.visibility == Visibility.INTERNAL
        
        # Check group config
        assert 'mygroup/*' in entities
        group = entities['mygroup/*']
        assert group.project_settings.get_inheritance() == "force"
        assert group.badges.is_enforced() is True
        assert len(group.badges.badges) == 2
        assert group.members.is_enforced() is True
        assert len(group.members.users) == 2
        assert group.group_push_rules is not None
        
        # Check project config
        assert 'mygroup/special-project' in entities
        project = entities['mygroup/special-project']
        assert project.project_settings.visibility == Visibility.PRIVATE
        assert len(project.project_settings.topics) == 2

    def test_usage_pattern_for_applying_configs(self):
        """Test the usage pattern: iterate configs and apply to groups/projects."""
        config = """
        projects_and_groups:
          group1/*:
            project_settings:
              visibility: internal
            badges:
              coverage:
                name: "Coverage"
                link_url: "http://example.com"
            members:
              users:
                user1:
                  access_level: maintainer
        """
        
        entities = parse_typed_config_v5(config)
        
        # Simulate the usage pattern from the comment
        for entity_path, entity_config in entities.items():
            # Get all configuration objects for this entity
            configs = entity_config.get_configs()
            
            # Simulate getting groups/projects based on path
            # (In real usage, this would query GitLab API)
            if entity_config.is_group():
                # This is a group configuration
                groups_to_apply = [entity_path]  # Would be actual groups
            else:
                # This is a project configuration
                projects_to_apply = [entity_path]  # Would be actual projects
            
            # Apply each configuration
            for config_obj in configs:
                config_type = type(config_obj).__name__
                
                # Each config object has methods to check directives
                if hasattr(config_obj, 'is_enforced'):
                    is_enforced = config_obj.is_enforced()
                
                if hasattr(config_obj, 'get_inheritance'):
                    inheritance = config_obj.get_inheritance()
                
                # Would apply the config to GitLab here
                # e.g., if isinstance(config_obj, BadgesConfig):
                #          apply_badges(project, config_obj)
        
        # Verify we got the expected configs
        group_entity = entities['group1/*']
        configs = group_entity.get_configs()
        assert len(configs) == 3  # project_settings, badges, members

    def test_raw_parameters_with_complex_types(self):
        """Test that raw parameters can contain strings, dicts, lists, numbers, bools."""
        parser = ConfigV5TypedParser()
        config = """
        projects_and_groups:
          group1/project1:
            project_settings:
              visibility: internal
              raw:
                simple_string: "text value"
                number_int: 42
                number_float: 3.14
                boolean_true: true
                boolean_false: false
                list_param: [1, 2, 3, "four"]
                nested_dict:
                  level1:
                    level2: "deep value"
                    level2_list: [a, b, c]
                  another_key: 100
                mixed_list:
                  - item1
                  - nested: {key: value}
                  - 42
        """
        entities = parser.parse(config)
        
        assert 'group1/project1' in entities
        entity = entities['group1/project1']
        
        # Verify raw parameters
        assert entity.project_settings is not None
        raw = entity.project_settings.get_raw_parameters()
        
        # Check different types
        assert raw['simple_string'] == "text value"
        assert raw['number_int'] == 42
        assert raw['number_float'] == 3.14
        assert raw['boolean_true'] is True
        assert raw['boolean_false'] is False
        assert raw['list_param'] == [1, 2, 3, "four"]
        
        # Check nested dict
        assert 'nested_dict' in raw
        assert raw['nested_dict']['level1']['level2'] == "deep value"
        assert raw['nested_dict']['level1']['level2_list'] == ['a', 'b', 'c']
        assert raw['nested_dict']['another_key'] == 100
        
        # Check mixed list
        assert len(raw['mixed_list']) == 3
        assert raw['mixed_list'][0] == 'item1'
        assert raw['mixed_list'][1] == {'nested': {'key': 'value'}}
        assert raw['mixed_list'][2] == 42
