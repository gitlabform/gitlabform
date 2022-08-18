# Resource Group

## Update Process Mode

This section purpose is to manage the [resource group process modes](https://docs.gitlab.com/ee/ci/resource_groups/#process-modes).

The key names are the resource group names associated to the project.

The value for each key name is a key-value pair. `process_mode` is the key and the value is one of the process modes defined [here](https://docs.gitlab.com/ee/ci/resource_groups/#change-the-process-mode).


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
