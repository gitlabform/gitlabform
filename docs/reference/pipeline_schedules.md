# Pipeline schedules

This section purpose is to manage the [pipeline schedules](https://docs.gitlab.com/ee/ci/pipelines/schedules.html).

The key name are schedule description (_GitLab Web Console_) and values are parameters described in the [Pipeline schedules API docs](https://docs.gitlab.com/ee/api/pipeline_schedules.html#create-a-new-pipeline-schedule), **except the id**.

Additionally, under a `variables` key you can add the pipeline schedule variables. The syntax here is that key name is the variable name, the value is under `value` and the optional `variable_type` can be set to `env_var` (default) or `file`.

!!! warning

    * If there are multiple pipeline schedules with the same key name in a single project, this will cause those schedules to be DELETED and replaced with the one from the configuration.

    * Do not set `description` attribute - see [#535](https://github.com/gitlabform/gitlabform/issues/535#issue-1678509984)

There are 2 gitlabform specific keys/configs that can be set under `schedules` or individual schedule:

- `delete` - set this to `true` under a specific schedule to delete that particular schedule.
- `enforce` - set this to `true` under `schedules` so that any schedules that are not in `schedules` section are deleted.

    !!! warning

        The `delete` key maybe removed in future version of gitlabform as `enforce` key can be used for deleteing unconfigured schedules and keep gitlabform config cleaner.


Example 1:
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
        delete: true  # Delete this schedule
```

Example 2:
```yaml
projects_and_groups:
  group_1/project_1:
    schedules:
      enforce: true  # Delete all other pipeline schedules that exists for this project
      "Some schedule":
        ref: main
        cron: "0 * * * MON-FRI"
        cron_timezone: "London"
        active: false
```
