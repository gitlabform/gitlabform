# Config v5: Syntax Comparison and Recommendations

This document compares the different approaches for implementing configuration control in GitLabForm v5.

## The Challenge

The goal is to add configuration control directives (`inherit`, `enforce`, `delete`, `keep_existing`) without cluttering the JSON Schema with these keys everywhere.

## Approach Comparison

### 1. YAML Custom Tags (Implemented) ⭐ Recommended

**Syntax:**
```yaml
project_settings: !inherit force
topics: !keep_existing
  - !delete topicA
  - topicB
members:
  !enforce
  users:
    admin:
      access_level: maintainer
```

**Pros:**
- ✅ Clean syntax
- ✅ Doesn't pollute configuration namespace
- ✅ Tags are automatically filtered during processing
- ✅ Type-safe with validation at parse time
- ✅ Follows YAML standard for extensions

**Cons:**
- ❌ Requires understanding YAML tag syntax
- ❌ Tags must be on same line as key (YAML limitation)
- ❌ Requires custom YAML parser (ruamel.yaml)

**When to use:** Default choice for new configurations.

---

### 2. Special Key Prefixes (Implemented) 🔄 Alternative

**Syntax:**
```yaml
project_settings:
  _inherit: force
topics:
  _keep_existing: true
  - topicA
  - topicB
members:
  _enforce: true
  users:
    admin:
      access_level: maintainer
```

**Pros:**
- ✅ Works with any YAML parser
- ✅ No YAML tag syntax limitations
- ✅ Easy to understand
- ✅ Can be used anywhere in hierarchy

**Cons:**
- ❌ Control keys visible in configuration namespace
- ❌ Need to be filtered during processing
- ❌ Slightly more verbose

**When to use:** When YAML tag syntax is too restrictive, or when using external YAML tools that don't support custom tags.

---

### 3. Metadata Section Approach ❌ Not Recommended

**Syntax:**
```yaml
project_settings:
  _meta:
    inherit: force
  _config:
    visibility: internal
    topics:
      - topicA
```

**Pros:**
- ✅ Clear separation of metadata
- ✅ Works with standard YAML

**Cons:**
- ❌ Very verbose
- ❌ Changes data structure significantly
- ❌ Harder to read and maintain

**When to use:** Not recommended for GitLabForm.

---

### 4. YAML Comments with Parser ❌ Not Recommended

**Syntax:**
```yaml
project_settings:  # @inherit force
  topics:  # @keep_existing
    - topicA  # @delete
```

**Pros:**
- ✅ Looks clean
- ✅ Doesn't affect YAML structure

**Cons:**
- ❌ Requires custom comment parser
- ❌ Comments can be stripped by YAML processors
- ❌ Brittle and error-prone
- ❌ Not standard YAML

**When to use:** Not recommended.

---

## Syntax Limitations and Solutions

### The Original Request

The issue requested this syntax:
```yaml
project_settings: 
  !inherit force
  topics:
    !keep_existing
    - !delete topicA
    - topicB
```

**Problem:** This syntax is **invalid YAML** because tags must appear on the same line as the key or at the start of a block node.

### Working Alternatives

#### Option A: YAML Tags (Current Implementation)
```yaml
# ✅ Tag on same line
project_settings: !inherit force

# ✅ Tag with list
topics: !keep_existing
  - !delete topicA
  - topicB

# ✅ Tag on block mapping
members:
  !enforce
  users:
    admin:
      access_level: maintainer
```

#### Option B: Special Keys (Alternative)
```yaml
# ✅ Standard YAML - no tag restrictions
project_settings:
  _inherit: force
  topics:
    _keep_existing: true
    - topicA
    - topicB
```

## Real-World Examples

### Example 1: Group Configuration with Inheritance

**YAML Tags Approach:**
```yaml
projects_and_groups:
  "*":
    project_settings:
      visibility: internal
  
  mygroup/*:
    project_settings: !inherit force
    topics: !keep_existing
      - security
      - compliance
    members:
      !enforce
      users:
        admin:
          access_level: maintainer
```

**Special Keys Approach:**
```yaml
projects_and_groups:
  "*":
    project_settings:
      visibility: internal
  
  mygroup/*:
    project_settings:
      _inherit: force
    topics:
      _keep_existing: true
      - security
      - compliance
    members:
      _enforce: true
      users:
        admin:
          access_level: maintainer
```

### Example 2: Project with Deletions

**YAML Tags Approach:**
```yaml
mygroup/myproject:
  topics:
    - !delete legacy-topic
    - !delete deprecated-topic
    - new-topic
    - active-topic
```

**Special Keys Approach:**
```yaml
mygroup/myproject:
  topics:
    - name: legacy-topic
      _delete: true
    - name: deprecated-topic
      _delete: true
    - new-topic
    - active-topic
```

## Recommendations

### For New Configurations
Use **YAML Tags** (Approach 1) because:
- Cleaner syntax
- Doesn't pollute namespace
- More powerful and flexible

### For Compatibility/Migration
Use **Special Keys** (Approach 2) when:
- Migrating from v3/v4 with existing tooling
- Using external YAML validation tools
- YAML tag syntax limitations are problematic
- Need maximum compatibility

### For Maximum Flexibility
You can even **mix both approaches** in the same configuration:
```yaml
projects_and_groups:
  group1/*:
    project_settings: !inherit force  # Tag approach
    topics:
      _keep_existing: true            # Special key approach
      - new-topic
```

## Implementation Status

| Feature | YAML Tags | Special Keys | Status |
|---------|-----------|--------------|--------|
| `!inherit` / `_inherit` | ✅ | ✅ | Implemented |
| `!enforce` / `_enforce` | ✅ | ✅ | Implemented |
| `!delete` / `_delete` | ✅ | ✅ | Implemented |
| `!keep_existing` / `_keep_existing` | ✅ | ✅ | Implemented |
| `!include` / `_include` | ✅ | 🔄 | Tags only |
| Unit Tests | ✅ 25 tests | ✅ 19 tests | Complete |
| Documentation | ✅ | ✅ | Complete |
| Integration with config parsing | 🔄 | 🔄 | Future work |

## Migration Path

### From Config v3/v4

**Old:**
```yaml
project_settings:
  inherit: false  # Control key in namespace
  visibility: internal
```

**New (Tags):**
```yaml
project_settings: !inherit false
visibility: internal
```

**New (Special Keys):**
```yaml
project_settings:
  _inherit: false
  visibility: internal
```

## Testing

Both approaches have comprehensive test suites:

```bash
# Test YAML tags
pytest tests/unit/configuration/test_yaml_tags.py -v

# Test special keys
pytest tests/unit/configuration/test_special_keys.py -v

# Test both together
pytest tests/unit/configuration/ -v
```

## Conclusion

GitLabForm v5 provides **two complementary approaches** for configuration control:

1. **YAML Tags** - Recommended for most use cases
2. **Special Keys** - Alternative when tags are too restrictive

Both achieve the same functionality without cluttering the JSON Schema. Choose based on your specific needs and constraints.
