# Settings

## Application Settings

This section purpose it to manage the [Application settings](https://docs.gitlab.com/ee/api/settings.html).

You can provide any number of the settings from there - if you don't provide a setting then it will be not changed.

Example:

```yaml
application:
  settings:
    asset_proxy_allowlist: ["example.com", "*.example.com", "your-instance.com"]
    require_two_factor_authentication: true
    two_factor_grace_period: 2
projects_and_groups:
  group_1/project_1:
    project_settings:
      default_branch: main
```

## Project Settings

This section purpose is to manage the [project settings](https://docs.gitlab.com/ee/user/project/settings/).

The settings should be as documented at GitLab's [Project API docs](https://docs.gitlab.com/ee/api/projects.html#edit-project), **except the id**.

You can provide any number of the settings from there - if you don't provide a setting then it will be not changed.

Note that some keys and values can be very complex here - see the [Container Registry cleanup policies](https://docs.gitlab.com/ee/user/packages/container_registry/reduce_container_registry_storage.html#use-the-cleanup-policy-api) under the `container_expiration_policy_attributes` key in the code below as an example.

!!! note

    Some [Merge Requests](merge_requests.md)-related settings are also set here.

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
      duo_features_enabled: false
      container_expiration_policy_attributes:
        cadence: "1month"
        enabled: true
        keep_n: 1
        older_than: "14d"
        name_regex: ""
        name_regex_delete: ".*"
        name_regex_keep: ".*-main"
      # (...)
```

### Project Settings - GitLab Duo
We have extended the functionality of GitLabForm to support setting `duo_features_enabled` at the Project Level, which are currently supported in the [Group Setting API](https://docs.gitlab.com/api/groups/#update-group-attributes), but only via GraphQL for Projects.

You can specify `duo_features_enabled: true` or `false` under the `project_settings` configuration and GitLabForm will make the appropriate [GraphQL Mutation](https://gitlab.com/gitlab-org/gitlab/-/issues/571776) to update the Project Settings.

### Project Settings - Topics

GitLab's [project settings API](https://docs.gitlab.com/ee/api/projects.html#edit-a-project) takes a list of string to be used as project topics. It will overwrite any existing topics that may exist. GitLabForm allows special configuration if finer control is needed for managing project topics.

Generally a list of string under `topics` will be used as-is. Those strings will be set as project topics.

GitLabForm will accept additional configuration under `topics`. An item in the list can be an object whose key is `keep_existing` that expects boolean value. If this object is set and the value is set to `true`, existing topics will be kept by including them in the list of project topics when they are updated via GitLab API.

If a specific topic should be deleted, it can be configured as an object containing `delete: true`. See the example below.

Examples:

```yaml
projects_and_groups:
  group_1/project_1:
    projects_settings:
      topics:
        - keep_existing: true
        - topicA
        - topicB
        - topicC:
            delete: true
```


## Group Settings

This section purpose is to manage the [group settings](https://docs.gitlab.com/ee/user/group/).

The settings should be as documented at GitLab's [Groups API docs](https://docs.gitlab.com/ee/api/groups.html#update-group), **except the id**.

You can provide any number of the settings from there - if you don't provide a setting then it will be not changed.

```yaml
projects_and_groups:
  group_1/*:
    # configures settings for the 'group-with-spammy-projects' group
    group_settings:
      # keys and values here are as described at https://docs.gitlab.com/ee/api/groups.html#update-group
      emails_disabled: true
```
