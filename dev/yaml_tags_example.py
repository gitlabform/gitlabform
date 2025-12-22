#!/usr/bin/env python3
"""
Example script demonstrating the usage of custom YAML tags in GitLabForm config v5.

This script shows how the new YAML tags can be used to control configuration behavior
without cluttering the JSON Schema with special keys everywhere.

Tags supported:
- !inherit: Control configuration inheritance (values: true, false, never, always, force)
- !enforce: Enforce configuration settings
- !delete: Mark items for deletion
- !keep_existing: Keep existing values when merging
- !include: Include external YAML files
"""

import sys
import ruamel.yaml
from gitlabform.configuration.yaml_tags import register_custom_tags


def demonstrate_yaml_tags():
    """Demonstrate the usage of custom YAML tags."""

    # Create a YAML parser with custom tags registered
    yaml = ruamel.yaml.YAML()
    register_custom_tags(yaml)

    # Example 1: Using !inherit to control inheritance
    print("=" * 80)
    print("Example 1: Using !inherit tag to force inheritance")
    print("=" * 80)
    config1 = """
    projects_and_groups:
      group1/*:
        project_settings: !inherit force
        topics:
          - topicA
          - topicB
    """
    parsed1 = yaml.load(config1)
    print("Configuration YAML:")
    print(config1)
    print(f"Inherit tag value: {parsed1['projects_and_groups']['group1/*']['project_settings'].get_tag('inherit')}")
    print(f"Topics: {list(parsed1['projects_and_groups']['group1/*']['topics'])}")
    print()

    # Example 2: Using !delete to mark items for deletion
    print("=" * 80)
    print("Example 2: Using !delete tag to mark items for deletion")
    print("=" * 80)
    config2 = """
    project_settings:
      topics:
        - !delete topicA  # delete topicA if it already exists
        - topicB
        - topicC
    """
    parsed2 = yaml.load(config2)
    print("Configuration YAML:")
    print(config2)
    topics = parsed2['project_settings']['topics']
    print(f"First topic value: {topics[0].value if hasattr(topics[0], 'value') else topics[0]}")
    print(f"First topic has delete tag: {topics[0].get_tag('delete') if hasattr(topics[0], 'get_tag') else False}")
    print(f"Other topics: {[t.value if hasattr(t, 'value') else t for t in topics[1:]]}")
    print()

    # Example 3: Using !keep_existing to preserve existing values
    print("=" * 80)
    print("Example 3: Using !keep_existing tag to preserve existing values")
    print("=" * 80)
    config3 = """
    project_settings:
      topics: !keep_existing
        - newTopic1
        - newTopic2
    """
    parsed3 = yaml.load(config3)
    print("Configuration YAML:")
    print(config3)
    print(f"Keep existing tag: {parsed3['project_settings']['topics'].get_tag('keep_existing')}")
    print(f"Topics: {list(parsed3['project_settings']['topics'])}")
    print()

    # Example 4: Using !enforce to enforce configuration
    print("=" * 80)
    print("Example 4: Using !enforce tag to enforce configuration")
    print("=" * 80)
    config4 = """
    project_settings:
      !enforce
      members:
        users:
          user1:
            access_level: maintainer
    """
    parsed4 = yaml.load(config4)
    print("Configuration YAML:")
    print(config4)
    print(f"Enforce tag value: {parsed4['project_settings'].get_tag('enforce')}")
    print(f"Members: {dict(parsed4['project_settings'])}")
    print()

    # Example 5: Complex example with multiple tags
    print("=" * 80)
    print("Example 5: Complex configuration with multiple tags")
    print("=" * 80)
    config5 = """
    projects_and_groups:
      group1/*:
        project_settings: !inherit force
        topics: !keep_existing
          - !delete oldTopic
          - newTopic
        members:
          !enforce
          users:
            user1:
              access_level: maintainer
            user2:
              access_level: developer
    """
    parsed5 = yaml.load(config5)
    print("Configuration YAML:")
    print(config5)
    group_config = parsed5['projects_and_groups']['group1/*']
    print(f"Project settings inherit tag: {group_config['project_settings'].get_tag('inherit')}")
    print(f"Topics keep_existing tag: {group_config['topics'].get_tag('keep_existing')}")
    print(f"First topic value: {group_config['topics'][0].value if hasattr(group_config['topics'][0], 'value') else group_config['topics'][0]}")
    print(f"First topic delete tag: {group_config['topics'][0].get_tag('delete') if hasattr(group_config['topics'][0], 'get_tag') else False}")
    print(f"Members enforce tag: {group_config['members'].get_tag('enforce')}")
    print()

    # Example 6: Using !inherit with sequence for combinations
    print("=" * 80)
    print("Example 6: Using !inherit with sequence for tag combinations")
    print("=" * 80)
    config6 = """
    project_settings: !inherit [always, keep_existing]
    """
    parsed6 = yaml.load(config6)
    print("Configuration YAML:")
    print(config6)
    print(f"Inherit tag: {parsed6['project_settings'].get_tag('inherit')}")
    print(f"Keep existing tag: {parsed6['project_settings'].get_tag('keep_existing')}")
    print()

    print("=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        demonstrate_yaml_tags()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
