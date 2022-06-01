# Archive/unarchive project

This section purpose is to [archive a project](https://docs.gitlab.com/ee/user/project/settings/#archiving-a-project) or revert this process - unarchive it.

There can be only one key under this section - `archive` - set to `true` or `false`.

!!! important

    To unarchive a project you must run GitLabForm with the `--include-archived-projects` cli parameter, as by default the app skips the archived projects when it gathers the list of projects to process.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    project:
      archive: true
```
