# Project Settings

This section purpose is to manage the [project settings](https://docs.gitlab.com/ee/user/project/settings/).

The settings should be as documented at GitLab's [Project API docs](https://docs.gitlab.com/ee/api/projects.html#edit-project), **except the id**.

You can provide any number of the settings from there - if you don't provide a setting then it will be not changed.

!!! note

    Some [Merge Requests][merge_requests]-related settings are also set here.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    project_settings:
      default_branch: main
      builds_access_level: enabled
      visibility: internal
      only_allow_merge_if_pipeline_succeeds: true
      only_allow_merge_if_all_discussions_are_resolved: true
      # (...)
```
