# Topics


## Projects Topics

This section purpose is to manage the [project topics](https://docs.gitlab.com/ee/api/projects.html#edit-a-project) which are part of project settings.

Using [Project Settings](./settings.md#project-settings) only allows for topics to be overwritten.


## Project Push rules

Examples:

```yaml
projects_and_groups:
  group_1/project_1:
    project_topics:
      topics:
        - topicA
        - topicB
        - topicC
```

```yaml
projects_and_groups:
  group_1/project_1:
    project_topics:
      topics:
        - topicA
        - topicB
            delete: true
```

```yaml
projects_and_groups:
  group_1/project_1:
    project_topics:
      topics:
        - topicA
        - topicB
      enforce: true

```

