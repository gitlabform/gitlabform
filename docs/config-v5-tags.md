# Configuration v5: Custom YAML Tags

GitLabForm configuration v5 introduces custom YAML tags that allow fine-grained control over configuration behavior without cluttering the JSON Schema with special keys everywhere.

## Overview

The following custom YAML tags are supported:

- `!inherit` - Control configuration inheritance
- `!enforce` - Enforce configuration settings
- `!delete` - Mark items for deletion
- `!keep_existing` - Keep existing values when merging
- `!include` - Include external YAML files

These tags can be used anywhere in the configuration to modify how settings are processed and applied to GitLab groups and projects.

## Tag Reference

### !inherit

Controls how configuration is inherited from parent levels (common → group → project).

**Valid values:**
- `true` - Allow inheritance (default behavior)
- `false` - Break inheritance at this level
- `never` - Never inherit from parent levels
- `always` - Always inherit, even if normally skipped
- `force` - Force inheritance, overriding any restrictions

**Usage examples:**

```yaml
# Force inheritance of project settings
projects_and_groups:
  group1/*:
    project_settings: !inherit force
    topics:
      - topicA
      - topicB
```

```yaml
# Break inheritance at a specific level
projects_and_groups:
  group1/*:
    members: !inherit false
    users:
      user1:
        access_level: maintainer
```

```yaml
# Combine inherit with keep_existing
projects_and_groups:
  group1/*:
    topics: !inherit [always, keep_existing]
```

### !enforce

Enforces configuration settings, ensuring they are applied exactly as specified.

**Usage examples:**

```yaml
# Enforce member configuration
projects_and_groups:
  group1/*:
    members:
      !enforce
      users:
        user1:
          access_level: maintainer
        user2:
          access_level: developer
```

```yaml
# Enforce project settings
project_settings:
  !enforce
  topics:
    - topic1
    - topic2
  variables:
    VAR1: value1
    VAR2: value2
```

### !delete

Marks specific items for deletion. This is useful when you want to remove existing items from GitLab while adding or keeping others.

**Usage examples:**

```yaml
# Delete specific topics
project_settings:
  topics:
    - !delete oldTopic    # This topic will be removed
    - newTopic            # This topic will be added
    - !delete deprecated  # This will also be removed
```

```yaml
# Delete specific variables
variables:
  - !delete OLD_VAR
  - NEW_VAR: new_value
```

### !keep_existing

Preserves existing values in GitLab when merging configuration. Instead of replacing existing items, new items are added to the existing ones.

**Usage examples:**

```yaml
# Keep existing topics and add new ones
project_settings:
  topics: !keep_existing
    - newTopic1
    - newTopic2
```

```yaml
# Keep existing members and add new ones
members:
  users: !keep_existing
    new_user:
      access_level: developer
```

### !include

Includes configuration from external YAML files. This is useful for splitting large configurations into smaller, reusable files.

**Usage examples:**

```yaml
# Include common settings from external file
projects_and_groups:
  "*": !include common-settings.yml
```

```yaml
# Include group-specific settings
projects_and_groups:
  mygroup/*: !include groups/mygroup.yml
```

**Note:** The included file can also contain custom YAML tags, which will be processed recursively.

## Complete Example

Here's a comprehensive example showing multiple tags working together:

```yaml
config_version: 5

projects_and_groups:
  "*":
    # Common settings for all projects
    project_settings:
      visibility: internal
    
  mygroup/*:
    # Force inheritance of project settings
    project_settings: !inherit force
    
    # Keep existing topics and add new ones, but delete deprecated
    topics: !keep_existing
      - !delete legacy-topic
      - security
      - compliance
    
    # Enforce member configuration
    members:
      !enforce
      users:
        admin-user:
          access_level: maintainer
        dev-user:
          access_level: developer
  
  mygroup/special-project:
    # Break inheritance for this specific project
    project_settings: !inherit false
    
    # Project-specific topics without keeping existing
    topics:
      - internal
      - confidential
```

## Tag Combinations

Some tags can be combined for more complex behavior:

### inherit + keep_existing

```yaml
topics: !inherit [always, keep_existing]
```

This ensures inheritance is always applied AND existing values are kept.

## Migration from v3/v4

If you're migrating from configuration v3 or v4, here's how the new tags map to old behavior:

| Old Approach | New Approach |
|-------------|-------------|
| `inherit: false` (as a key) | `!inherit false` (as a tag) |
| `enforce: true` (as a key) | `!enforce` (as a tag) |
| Manual deletion in scripts | `!delete item` (in config) |
| Complex merging logic | `!keep_existing` (simple tag) |
| Multiple config files | `!include file.yml` (built-in) |

## Benefits

The custom YAML tags approach provides several benefits:

1. **Cleaner Schema**: Special control keys don't pollute the JSON Schema
2. **More Flexible**: Tags can be applied anywhere, not just at specific levels
3. **More Intuitive**: Tags clearly indicate intent (e.g., `!delete` vs checking a boolean)
4. **Composable**: Multiple tags can work together for complex scenarios
5. **Type-Safe**: Invalid tag values are caught at parse time

## Implementation Details

The custom tags are implemented using ruamel.yaml's constructor mechanism. Each tag has a corresponding constructor function that creates custom data structures to track the tag metadata alongside the actual configuration values.

### Data Structures

- `GitLabFormTagOrderedDict`: Mapping nodes (dicts) with tag metadata
- `GitLabFormTagList`: Sequence nodes (lists) with tag metadata  
- `GitLabFormTagScalar`: Scalar values with tag metadata

These structures maintain the tag information throughout configuration processing, allowing the application logic to inspect and act on the tags.

## Testing

Comprehensive unit tests are available in `tests/unit/configuration/test_yaml_tags.py`. Run them with:

```bash
pytest tests/unit/configuration/test_yaml_tags.py -v
```

## Example Script

A demonstration script is available at `dev/yaml_tags_example.py` that shows all tags in action:

```bash
python dev/yaml_tags_example.py
```

## Future Enhancements

Potential future enhancements to the tag system:

- Additional tags for specific use cases
- Tag parameters for more fine-grained control
- Custom user-defined tags via plugins
- Tag validation against JSON Schema
- IDE support for tag completion and validation
