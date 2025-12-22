# Config v5: Questions and Answers

## Q1: How does the block mapping tag syntax work?

**Question:** How come this works when "❌ Tags must be on same line as key (YAML limitation)":

```yaml
# ✅ Tag on block mapping
members:
  !enforce
  users:
    admin:
      access_level: maintainer
```

**Answer:**

This works because the tag `!enforce` appears **immediately before** the mapping content it modifies. In YAML terms:

- `members:` is a key with an empty value initially
- `!enforce` is a tag directive that applies to the **next node**
- The indented block `users: {...}` is that next node - a mapping
- The tag modifies how the entire mapping is parsed

**Key principle:** Tags modify the **immediately following node**. In this case, the tag appears at the start of the block content, which is valid YAML.

### What Makes This Valid

```yaml
members:          # Key
  !enforce        # Tag for the following mapping
  users:          # Start of mapping (the node being tagged)
    admin:
      access_level: maintainer
```

The tag is not "on a separate line after the key" - it's "at the start of the block value".

### What Doesn't Work

```yaml
project_settings:     # Key
  !inherit force      # This tries to tag "force" as a scalar
  topics:             # This becomes a sibling key - INVALID YAML
    - topicA
```

Here, `!inherit force` creates a tagged scalar "force", then `topics:` tries to be another key at the same level, which creates a syntax error because you can't have multiple values for one key.

### Visual Comparison

**Valid (block mapping tag):**
```
key:
  !tag
  content
```
Structure: `key` → value is a tagged mapping

**Invalid (separated content):**
```
key:
  !tag value
  other_key: data
```
Structure: Tries to have `key` → `!tag value` AND `key` → `other_key: data` (ambiguous)

## Q2: When are Special Keys needed vs YAML Tags?

**Question:** Are there any known cases where YAML Tags can't be used and Special Keys are needed?

**Answer:**

Yes, there are several scenarios where Special Keys (`_inherit`, `_enforce`, etc.) may be preferred or required:

### 1. **Tool Compatibility Issues**

Many YAML tools don't support custom tags:

```bash
# Tools that may not support custom tags:
- yamllint (may flag custom tags as errors)
- Online YAML validators
- IDE YAML plugins (may not recognize custom tags)
- Generic YAML→JSON converters
```

With special keys, these tools work without modification.

### 2. **Pre-processing Requirements**

If you need to pre-process YAML before GitLabForm sees it:

```yaml
# With special keys - standard YAML, works everywhere
project_settings:
  _inherit: force
  visibility: ${ENV_VAR}  # Can use standard tools to substitute
```

### 3. **Migration from Existing Configs**

If migrating from v3/v4 where control keys were normal keys:

```yaml
# v3/v4 style
project_settings:
  inherit: false
  visibility: internal

# Easy migration to v5 with special keys
project_settings:
  _inherit: false  # Just add underscore
  visibility: internal

# Harder migration to v5 with tags
project_settings: !inherit false  # Requires restructuring
visibility: internal
```

### 4. **Dynamic Configuration Generation**

When generating configs programmatically:

```python
# Easier with special keys
config = {
    "project_settings": {
        "_inherit": "force",
        "visibility": "internal"
    }
}

# vs tags requiring special YAML objects
from gitlabform.configuration.yaml_tags import GitLabFormTagOrderedDict
config = {
    "project_settings": GitLabFormTagOrderedDict()
}
config["project_settings"].set_tag("inherit", "force")
config["project_settings"]["visibility"] = "internal"
```

### 5. **Documentation and Examples**

Special keys are more intuitive in documentation:

```yaml
# Clear what _inherit does just by reading
project_settings:
  _inherit: force
  
# Requires understanding YAML tags
project_settings: !inherit force
```

### 6. **No Syntax Limitations**

Special keys have no YAML placement restrictions:

```yaml
# Special keys can go anywhere
deeply:
  nested:
    structure:
      with:
        any:
          level:
            _inherit: force
            _enforce: true
```

### Recommendation

**Use YAML Tags when:**
- Working entirely within GitLabForm
- Want clean namespace (no control keys in config)
- Understand YAML tag syntax
- Using ruamel.yaml parser

**Use Special Keys when:**
- Need tool compatibility
- Migrating from older versions
- Generating configs programmatically
- Need maximum flexibility
- Working with team members unfamiliar with YAML tags

**Both approaches are fully supported and can be mixed in the same configuration.**

## Q3: Examples of Non-Working Tag Syntax

**Question:** In the docs these two are listed as not working:
- ❌ Tags on indented lines (YAML limitation)
- ❌ Tags separated from content (YAML limitation)

Please provide YAML examples of each for clarification.

**Answer:**

### Example 1: Tags on Indented Lines

**❌ DOESN'T WORK:**
```yaml
project_settings:
  !inherit force    # Tag on indented line AFTER key
  visibility: internal
  topics:
    - topicA
```

**Why it fails:** After `project_settings:`, the parser expects either:
- A scalar value on the same line: `project_settings: value`
- An indented block with mapping pairs: `project_settings:\n  key: value`

The tag `!inherit force` creates a tagged scalar "force", but then `visibility:` tries to be another key-value pair, which is invalid because `project_settings` can't have both a scalar value AND mapping children.

**Error message:**
```
mapping values are not allowed here
  in "<unicode string>", line 4, column 15:
      visibility: internal
                  ^ (line: 4)
```

**✅ CORRECT ALTERNATIVES:**

```yaml
# Option A: Tag on same line
project_settings: !inherit force

# Option B: Use special keys
project_settings:
  _inherit: force
  visibility: internal
  topics:
    - topicA
```

### Example 2: Tags Separated from Content

**❌ DOESN'T WORK:**
```yaml
topics:
  !keep_existing    # Tag on separate line
  - topicA          # List content
  - topicB
```

**Why it fails:** The tag `!keep_existing` appears alone on a line, then the list content `- topicA` appears below. YAML interprets this as trying to apply the tag to whatever scalar follows it, not the list.

**Error varies** - it might parse as:
```yaml
topics:
  <tagged_empty_value>  # !keep_existing creates this
  - topicA              # This becomes a sibling, causing structure error
```

**✅ CORRECT ALTERNATIVES:**

```yaml
# Option A: Tag on same line as key
topics: !keep_existing
  - topicA
  - topicB

# Option B: Tag with inline list (less readable)
topics: !keep_existing [topicA, topicB]

# Option C: Use special keys
topics:
  _keep_existing: true
  - topicA
  - topicB
```

### Example 3: Common Mistake - Tag in Middle of Block

**❌ DOESN'T WORK:**
```yaml
project_settings:
  visibility: internal
  !inherit force        # Tag in middle of mapping
  topics:
    - topicA
```

**Why it fails:** You can't put a tag in the middle of a mapping's key-value pairs. Tags must be at the start of a node.

**✅ CORRECT ALTERNATIVES:**

```yaml
# Option A: Tag at start of block (affects whole mapping)
project_settings:
  !inherit
  force: true           # If you want force as a value
  visibility: internal
  topics:
    - topicA

# Option B: Use special keys
project_settings:
  _inherit: force
  visibility: internal
  topics:
    - topicA
```

### Summary Table

| Incorrect Syntax | Why It Fails | Correct Alternative |
|------------------|--------------|---------------------|
| `key:`<br>`  !tag value`<br>`  other: data` | Tag creates scalar, then other key conflicts | `key: !tag value` or use `_tag: value` |
| `key:`<br>`  !tag`<br>`  - item` | Tag separated from list content | `key: !tag`<br>`  - item` |
| `key:`<br>`  data: 1`<br>`  !tag`<br>`  more: 2` | Tag can't be in middle of mapping | Tag at start or use `_tag` |

### The Golden Rule

**YAML tags must appear:**
1. On the same line as the key: `key: !tag value`
2. At the start of a block value: `key:`<br>`  !tag`<br>`  content`
3. Before the node they modify, with no intervening content

**They cannot appear:**
- On an indented line after a key with no clear node to tag
- Separated from their content by other keys or values
- In the middle of a mapping or sequence
