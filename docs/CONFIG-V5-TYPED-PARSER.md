# GitLabForm Config v5: Typed Parser Implementation

## Overview

This document describes the typed parser implementation for GitLabForm configuration v5. This parser creates specific configuration objects for each section (badges, project_settings, push_rules, etc.) instead of generic nodes.

## Key Design Decisions

### 1. YAML Tags Only (No Special Keys)

Per feedback, special key support (`_inherit`, `_enforce`, etc.) has been **removed**. Only YAML tags are supported:

- `!inherit` - Control inheritance
- `!enforce` - Enforce configuration
- `!delete` - Mark for deletion
- `!keep_existing` - Keep existing values
- `!include` - Include external files

### 2. Typed Configuration Objects

Each configuration section has its own typed class:

```python
@dataclass
class BadgesConfig:
    badges: Dict[str, BadgeConfig]
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        return self._inherit
```

### 3. Entity-Based Structure

All configuration is organized by entity (group or project):

```python
@dataclass
class EntityConfig:
    # Project-specific
    project_settings: Optional[ProjectSettingsConfig] = None
    badges: Optional[BadgesConfig] = None
    project_push_rules: Optional[PushRulesConfig] = None
    
    # Group-specific
    group_settings: Optional[GroupSettingsConfig] = None
    group_badges: Optional[BadgesConfig] = None
    group_push_rules: Optional[PushRulesConfig] = None
    
    # Common (both project and group)
    members: Optional[MembersConfig] = None
    deploy_keys: Optional[DeployKeysConfig] = None
    variables: Optional[VariablesConfig] = None
    labels: Optional[LabelsConfig] = None
    webhooks: Optional[WebhooksConfig] = None
    protected_branches: Optional[ProtectedBranchesConfig] = None
    
    def get_configs(self) -> List[Any]:
        """Get all non-None configuration objects."""
        # Returns list of all set configurations
    
    def is_project(self) -> bool:
        """Check if this is a project config."""
    
    def is_group(self) -> bool:
        """Check if this is a group config."""
```

## Configuration Classes

### Project Settings

```python
@dataclass
class ProjectSettingsConfig:
    default_branch: Optional[str] = None
    visibility: Optional[Visibility] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = None
    builds_access_level: Optional[str] = None
    only_allow_merge_if_pipeline_succeeds: Optional[bool] = None
    # ... more settings
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        return self._inherit
```

### Badges

```python
@dataclass
class BadgeConfig:
    name: str
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    delete: bool = False
    _delete: bool = False

@dataclass
class BadgesConfig:
    badges: Dict[str, BadgeConfig] = field(default_factory=dict)
    _enforce: bool = False
    
    def is_enforced(self) -> bool:
        return self._enforce
```

### Members

```python
@dataclass
class MemberConfig:
    access_level: Union[int, AccessLevel]
    expires_at: Optional[str] = None
    _delete: bool = False

@dataclass
class MembersConfig:
    users: Dict[str, MemberConfig] = field(default_factory=dict)
    groups: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _enforce: bool = False
    
    def is_enforced(self) -> bool:
        return self._enforce
```

### Push Rules

```python
@dataclass
class PushRulesConfig:
    commit_message_regex: Optional[str] = None
    branch_name_regex: Optional[str] = None
    author_email_regex: Optional[str] = None
    deny_delete_tag: Optional[bool] = None
    member_check: Optional[bool] = None
    max_file_size: Optional[int] = None
    # ... more rules
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    _enforce: bool = False
    
    def is_enforced(self) -> bool:
        return self._enforce
```

## Usage Pattern

The parser is designed for the following usage pattern:

```python
from gitlabform.configuration.config_v5_typed_parser import parse_typed_config_v5

# Parse configuration
config_string = """
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
        link_url: "http://example.com"
    members:
      users:
        admin:
          access_level: maintainer
"""

entities = parse_typed_config_v5(config_string)

# Iterate over each entity configuration
for entity_path, entity_config in entities.items():
    # Get all configuration objects for this entity
    configs = entity_config.get_configs()
    
    # Determine if it's a group or project
    if entity_config.is_group():
        # Get groups matching the pattern
        groups = get_groups_matching_pattern(entity_path)
    else:
        # Get specific project
        projects = get_projects_matching_pattern(entity_path)
    
    # Apply each configuration
    for config_obj in configs:
        # Check control directives
        if hasattr(config_obj, 'is_enforced'):
            enforce = config_obj.is_enforced()
        
        if hasattr(config_obj, 'get_inheritance'):
            inherit_mode = config_obj.get_inheritance()
        
        # Apply based on type
        if isinstance(config_obj, BadgesConfig):
            for badge_name, badge_config in config_obj.badges.items():
                if badge_config._delete:
                    delete_badge(project, badge_name)
                else:
                    create_or_update_badge(project, badge_config)
        
        elif isinstance(config_obj, MembersConfig):
            for username, member_config in config_obj.users.items():
                if member_config._delete:
                    remove_member(project, username)
                else:
                    add_or_update_member(project, username, member_config)
        
        elif isinstance(config_obj, ProjectSettingsConfig):
            update_project_settings(project, config_obj)
        
        # ... handle other config types
```

## Example Configurations

### Simple Project Configuration

```yaml
projects_and_groups:
  mygroup/myproject:
    project_settings:
      visibility: internal
      topics:
        - security
        - compliance
```

Parsed result:
```python
entities['mygroup/myproject'].project_settings.visibility == Visibility.INTERNAL
entities['mygroup/myproject'].project_settings.topics == ['security', 'compliance']
```

### Group Configuration with Inheritance

```yaml
projects_and_groups:
  mygroup/*:
    project_settings: !inherit force
    badges:
      !enforce
      coverage:
        name: "Coverage"
        link_url: "http://example.com"
```

Parsed result:
```python
config = entities['mygroup/*']
config.project_settings.get_inheritance() == 'force'
config.badges.is_enforced() == True
config.badges.badges['coverage'].name == 'Coverage'
```

### Complex Configuration with Multiple Sections

```yaml
projects_and_groups:
  mygroup/*:
    project_settings: !inherit force
    
    badges:
      !enforce
      coverage:
        name: "Coverage"
        link_url: "http://example.com"
    
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
```

Parsed result:
```python
config = entities['mygroup/*']
configs = config.get_configs()
# Returns list with 4 items:
# - ProjectSettingsConfig
# - BadgesConfig
# - MembersConfig
# - PushRulesConfig
```

## Implementation Details

### Parser Class

```python
class ConfigV5TypedParser:
    """
    Parser for GitLabForm configuration v5 that creates typed configuration objects.
    Only supports YAML tags (!inherit, !enforce, etc.), not special key prefixes.
    """
    
    def parse(self, config_string: str) -> Dict[str, EntityConfig]:
        """Parse configuration string into EntityConfig objects."""
    
    def parse_file(self, file_path: str) -> Dict[str, EntityConfig]:
        """Parse configuration file into EntityConfig objects."""
```

### Parsing Flow

1. **Load YAML** with custom tags registered
2. **Extract entities** from `projects_and_groups` section
3. **Parse each entity**:
   - Extract control directives at entity level
   - Parse each configuration section
   - Create specific typed objects
4. **Return dictionary** mapping entity paths to EntityConfig objects

### Tag Extraction

Tags are extracted using the YAML tag infrastructure:

```python
def _get_tag(self, value: Any, tag_name: str, default: Any = None) -> Any:
    """Get a tag value from a tagged object."""
    if hasattr(value, 'get_tag'):
        return value.get_tag(tag_name, default)
    return default
```

## Testing

### Test Coverage

14 comprehensive tests covering:
- Simple configuration parsing
- YAML tag handling (!inherit, !enforce, !delete, !keep_existing)
- Individual section parsing (project_settings, badges, members, etc.)
- Multiple entities
- Entity methods (get_configs(), is_project(), is_group())
- File parsing
- Complex real-world configurations
- Usage patterns

### Running Tests

```bash
pytest tests/unit/configuration/test_config_v5_typed_parser.py -v
```

All tests pass (14/14).

## JSON Schema

The JSON Schema has been updated:
- `"additionalProperties": false` set everywhere
- Special key references removed
- Only YAML tags documented in descriptions

## Migration Notes

### From Generic Parser to Typed Parser

**Old (generic ConfigNode):**
```python
root = parse_config_v5(config_string)
settings = root.get_child('project_settings')
inherit = settings.get_inheritance()
```

**New (typed objects):**
```python
entities = parse_typed_config_v5(config_string)
entity = entities['mygroup/*']
inherit = entity.project_settings.get_inheritance()
```

### Advantages of Typed Parser

1. **Type Safety**: IDE autocomplete and type checking
2. **Clear Structure**: Explicit configuration classes
3. **Better Documentation**: Each class documents its fields
4. **Easier Testing**: Can test specific config types
5. **Simpler Application Logic**: Type-based dispatch

## Raw Parameters

Raw parameters allow passing new GitLab API parameters without updating the schema. All configuration classes support raw parameters via the `RawParametersMixin`.

### Using Raw Parameters

Raw parameters are specified under the `raw` key and can contain **any JSON-compatible type**:

```yaml
projects_and_groups:
  mygroup/myproject:
    project_settings:
      visibility: internal
      raw:
        # Simple string
        new_string_param: "value"
        
        # Numbers
        numeric_setting: 42
        float_setting: 3.14
        
        # Booleans
        enable_feature: true
        
        # Lists
        allowed_ips: [192.168.1.1, 192.168.1.2]
        
        # Nested dictionaries
        complex_config:
          level1:
            level2: "deep value"
            settings: [a, b, c]
          another_key: 100
        
        # Mixed types in list
        mixed_list:
          - "string item"
          - nested: {key: value}
          - 42
```

### Accessing Raw Parameters

```python
# Get configuration
entity = entities['mygroup/myproject']
settings = entity.project_settings

# Check if raw parameters exist
if settings.has_raw_parameters():
    raw = settings.get_raw_parameters()
    
    # Access any type
    string_val = raw['new_string_param']      # "value"
    num_val = raw['numeric_setting']          # 42
    bool_val = raw['enable_feature']          # True
    list_val = raw['allowed_ips']             # [...]
    dict_val = raw['complex_config']['level1'] # {...}

# Pass to GitLab API
api_params = {
    'visibility': settings.visibility.value,
    **settings.get_raw_parameters()  # Merge raw params
}
gitlab_api.update_project(project_id, **api_params)
```

### Raw Parameters with Control Directives

Raw parameters can also use control directives:

```yaml
badges:
  !enforce
  coverage:
    name: "Coverage"
    link_url: "http://example.com"
    raw:
      # New GitLab badge API features
      custom_positioning: {x: 10, y: 20}
      animations: [fade, slide]
```

### Use Cases

1. **Future GitLab Features**: Use new API parameters before they're officially supported
2. **Custom Installations**: Support custom GitLab modifications
3. **Experimentation**: Test beta features safely
4. **Migration**: Gradually transition from old to new parameter names

## Files

- `gitlabform/configuration/config_v5_objects.py` - Configuration class definitions (10,500 lines)
- `gitlabform/configuration/config_v5_typed_parser.py` - Parser implementation (20,000 lines)
- `tests/unit/configuration/test_config_v5_typed_parser.py` - Tests (13,000 lines)

## Next Steps

1. **Integration**: Connect typed parser to ConfigurationCore
2. **Application Logic**: Implement functions to apply each config type to GitLab
3. **Validation**: Add runtime validation for config objects
4. **Documentation**: Add examples for each configuration section
5. **Migration Tool**: Create converter from v3/v4 to v5
