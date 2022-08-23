# Resource Group

## Prerequisite
A resource group must exist before the process mode can be updated. 

Add a resource group to a project by configuring it in your project's `gitlab-ci.yml` file. For more information, visit
https://docs.gitlab.com/ee/ci/resource_groups/#add-a-resource-group.

## Update Process Mode

This section's purpose is to manage the [resource group process modes](https://docs.gitlab.com/ee/ci/resource_groups/#process-modes).

The key names are the resource group names associated with the project.

The value for each key name is a key-value pair, with `process_mode` as the key and the value is one of the process 
modes defined [here](https://docs.gitlab.com/ee/ci/resource_groups/#change-the-process-mode).


Example:

```yaml
projects_and_groups:
  group_1/project_1:
    resource_group:
      staging: 
        process_mode: oldest_first
      production: 
        process_mode: newest_first
```
