# Resource Groups

## Prerequisite

A resource group must exist before the process mode can be updated, except if the key name `ensure_exists` is present and is set to `false`.

Add a resource group to a project by configuring it in your project's `gitlab-ci.yml` file. For more information, visit [the appropriate GitLab's docs](https://docs.gitlab.com/ee/ci/resource_groups/#add-a-resource-group).

## Update Process Mode

This section's purpose is to manage the [resource group process modes](https://docs.gitlab.com/ee/ci/resource_groups/#process-modes).

The key name `ensure_exists` is optional - if set to `false` it will not fail when trying to process a non-existent resource group; default is `true`.

The other key names are the resource group names associated with the project.
The value for each key name is a key-value pair, with `process_mode` as the key and the value is one of the process 
modes defined [here](https://docs.gitlab.com/ee/ci/resource_groups/#change-the-process-mode).

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    resource_groups:
      ensure_exists: false
      staging: 
        process_mode: oldest_first
      production: 
        process_mode: newest_first
      resource_group_that_dont_exist:
        process_mode: newest_first
```
