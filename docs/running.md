# Running

To apply settings for a single project, run the app with the path to the project, f.e.:

```shell
gitlabform my-group/my-project1
```

To apply settings for a group of projects, run:

```shell
gitlabform my-group
```

To apply settings for all groups of projects and projects explicitly defined in the config, run:

```shell
gitlabform ALL_DEFINED
```

To apply settings for all groups and projects that you can modify, run:

```shell
gitlabform ALL
```

To see what changes are being made, run:

```shell
gitlabform ALL_DEFINED --verbose
```

To see what changes are being made but limit the output to only those settings that are changing, run:

```shell
gitlabform -c config.yml ALL_DEFINED --verbose --diff-only-changed
```

Run:

```shell
gitlabform -h
```

...to see the current set of supported command line parameters.

## Command Line Options

To view the full set of Command Line Options you can run `gitlabform --help`

### Exclude Sections

To exclude certain sections of the configuration from a given gitlabform run, you can pass a list of comma-delimited names via the `--exclude-sections` parameter.

```shell
gitlabform --exclude-sections group-settings,project-settings
```

!!! warning

    gitlabform cannot guarantee consistent functionality when excluding and including different sections in executions of the tool, as Gitlab itself may require a specific set of operations. For example, provisioning of User and Group Permissions often needs to occur prior to other operations, we maintain a list within the `ProjectProcessors` and `GroupProcessors` classes in valid order of operations.