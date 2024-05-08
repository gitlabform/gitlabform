# Labels

This section purpose is to manage labels both [project](https://docs.gitlab.com/ee/api/labels.html) and [group](https://docs.gitlab.com/ee/api/group_labels.html)

## Project Labels

The keys name are as in the endpoints described in the [GitLab Labels API docs](https://docs.gitlab.com/ee/api/labels.html), f.e. `description`, `color` etc.

```yaml
projects_and_groups:
  group_1/project_1:
    labels:
      my_label:
        color: red
        description: hello world
```

`enforce` is used to determine whether labels present in GitLab but not the configuration should be deleted or not. Without enabled `enforce: true` we retain any labels not present in the configuration, to support automated tooling which may apply labels based on user's rulesets and work practices, such as for Compliance Frameworks.

```yaml
projects_and_groups:
  group_1/project_1:
    labels:
      enforce: true
      my_label:
        color: red
        description: hello world
```

The same project labels can be applied to all projects in a group using the following syntax:

```yaml
projects_and_groups:
  group_1/*:
    labels:
      my_label:
        color: red
        description: hello world
```

## Group Labels

The keys name are as in the endpoints described in the [GitLab Group Labels API docs](https://docs.gitlab.com/ee/api/group_labels.html), f.e. `description`, `color` etc.

We use `group_labels` as the key within the configuration to disambiguate from labels being applied to the Group and labels being applied to **all Projects** in a Group.

```yaml
projects_and_groups:
  group_1/*:
    group_labels:
      my_label:
        color: red
        description: hello world
```

`enforce` is used to determine whether labels present in GitLab but not the configuration should be deleted or not. Without enabled `enforce: true` we retain any labels not present in the configuration, to support automated tooling which may apply labels based on user's rulesets and work practices, such as for Compliance Frameworks.

```yaml
projects_and_groups:
  group_1/*:
    group_labels:
      enforce: true
      my_label:
        color: red
        description: hello world
```