# Pipeline schedules

This section purpose is to manage the [pipeline schedules](https://docs.gitlab.com/ee/ci/pipelines/schedules.html).

The keys name are schedule descriptions and values are parameters described in the [Pipeline schedules API docs](https://docs.gitlab.com/ee/api/pipeline_schedules.html#create-a-new-pipeline-schedule), **except the id**.

Additionally, under a `variables` key you can add the pipeline schedule variables. The syntax here is that key name is the variable name, the value is under `value` and the optional `variable_type` can be set to `env_var` (default) or `file`.

!!! warning

    If there are multiple pipeline schedules with the same description in a single project,
    this will cause those schedules to be DELETED and replaced with the one from the configuration.

Example:
```yaml
projects_and_groups:
  group_1/project_1:
    schedules:
      "Some schedule":
        ref: main
        cron: "0 * * * MON-FRI"
        cron_timezone: "London"
        active: false
      "Another schedule":
        ref: develop
        cron: "0 * * * *"
        variables:
          some_variable:
            value: some_value
            variable_type: file
          other_variable:
            value: another_value
      "Obsolete schedule":
        delete: true
```
