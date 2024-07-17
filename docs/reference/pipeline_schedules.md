# Pipeline schedules

## Basic use

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

    * Both a short version of a ref (e.g "main") and full version (e.g. "refs/heads/main") is accepted, GitLab will automatically expand short refs into full refs.

    * If the short ref is ambigious it will be rejected: https://docs.gitlab.com/ee/api/pipeline_schedules.html#create-a-new-pipeline-schedule

    * This appears to be more stringently enforced within GitLab 17.x


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

## Extended syntax

* There is an additional, extended syntax available for distributing pipelines automatically to avoid a pipeline stampede, see the [open issue at GitLab](https://gitlab.com/gitlab-org/gitlab/-/issues/17799) for some details.
* For **minutes**, **hours** and **weekdays** the uppercase letter ˚H will be replaced with stable, project specific values in the range of `0-59`, `0-23` resp `0-6`.
* There is a syntax for restricting the range: `H(15-20)` will return a value between 15 and 20.
* An interval like `H/20` e.g. in the minute column will firstly determine a value between 0 and 19 and then add corresponding entries to fill the as well, i.e. might give you `14,34,54` for the minutes. 
* This allows you to specify something like `H H(1-7) * * *` once as expression and each project will nonetheless get a different value for minute and hour, so your pipelines are distributed between 01:00 and 07:59 in above example.

Examples:

* Project with id 1: `H H * * *` -> `8 18 * * *`
* Project with id 3: `H H * * *` -> `15 18 * * *`
* Project with id 3: `H(15-20),H(45-50) H(1-7) * * *` -> `16,49 5 * * *`
* Project with id 4: `H H * * *` -> `15 9 * * *`

There are four (caseinsensitive) _aliases_ for ease of use similar to what exists in Jenkins:

* `@hourly` -> `H * * * *`
* `@daily` -> `H H * * *`
* `@weekly` -> `H H * * H`
* `@nightly` -> `H H(00-06) * * *`


