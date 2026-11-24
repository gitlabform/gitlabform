# Deploy freezes

This section purpose is to manage the project [Deploy freezes](https://docs.gitlab.com/ee/user/project/releases/#prevent-unintentional-releases-by-setting-a-deploy-freeze) (aka freeze periods).

Freeze periods are defined as a list under the `periods` key. Each period takes the parameters described at [create a freeze period](https://docs.gitlab.com/ee/api/freeze_periods.html#create-a-freeze-period): `freeze_start`, `freeze_end` (both cron expressions) and the optional `cron_timezone` (defaults to `UTC`).

The `periods` list is required. Periods missing in GitLab are created. GitLab freeze periods have no name, so a period is identified by all of its 3 values: changing a value is equivalent to adding a new period.

When `enforce` is set to `true`, the periods that exist in GitLab but are not in the list are deleted, so the list becomes the complete list of freeze periods of the project. Use `enforce: true` with an empty list (`periods: []`) to delete all of them.

If GitLab has several identical copies of a period from the list, only one is kept, even without `enforce`.

!!! note

    The `periods` list is not merged with the one inherited from a more general level (e.g. `group/*`) - a more specific list replaces it.

## Examples

Example 1: add these 2 freeze periods, keep any other periods already set in the project.

```yaml
projects_and_groups:
  group_1/project_1:
    deploy_freezes:
      periods:
        - freeze_start: "0 23 * * 5"
          freeze_end: "0 7 * * 1"
          cron_timezone: Europe/Paris
        - freeze_start: "0 0 24 12 *"
          freeze_end: "0 0 26 12 *"
```

Example 2: all projects in `group_1` will have only the weekend freeze period, except `project_1` that will have none.

```yaml
projects_and_groups:
  group_1/*:
    deploy_freezes:
      enforce: true
      periods:
        - freeze_start: "0 23 * * 5"
          freeze_end: "0 7 * * 1"
          cron_timezone: Europe/Paris
  group_1/project_1:
    deploy_freezes:
      periods: []
```
