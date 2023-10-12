# Transfer a resource

## Project transfer

This section describes [transferring a project](https://docs.gitlab.com/ee/user/project/settings/index.html#transfer-a-project-to-another-namespace) to another group or namespace.

Gitlabform supports `transfer_from` key under `project` map. Set the value to full path of the project including namespaces that needs to be transferred. See examples below.

!!! important

    Please note that Gitlab has specific requirements for project transfer. For example the user that runs gitlabform needs to be an owner of the project that will be transferred. See above docs referrence for detailed lists of prerequisites.

### Examples

In the example below, `group_2/project_1` project is configured to be transferred to `group_1` namespace.

```yaml
projects_and_groups:
  group_1/project_1:
    project:
      transfer_from: group_2/project_1
```

In subsequent runs of gitlabform, the transfer config will not take place because `group_1/project_1` already exists. Transfers can be done from subgroup or another root group/namespace too.

```yaml
projects_and_groups:
  group_1/foo/project_1:
    project:
      transfer_from: group_1/project_1

  group_1/project_2:
    project:
      transfer_from: group_1/bar/project_2
```

#### Transfer as new project path

It's also possible to change the project's path at the new location. In the example below, `project_1` path will be updated to `project_2` first and then transfer the project from the source group/namespace.

```yaml
projects_and_groups:
  group_1/project_2:
    project:
      transfer_from: group_2/project_1
```

Note that if `group_1` already contains a project with a path `project_2`, the transfer will not take place.

#### Transfer and update

Gitlabform processes different sections of a project's config in specific order. The `project` map/section is processed first. So, it's possible to transfer a project from another namespace first and then update that project according to the config.

```yaml
projects_and_groups:
  group_1/project_1:
    project:
      transfer_from: group_2/project_1
    project_settings:
      description: Hello world!
      # other project settings can be here
    branches:
      main:
        protected: true
        # other branch protection settings can be here
```

In the above example, `project_1` will be transferred from `group_2` to `group_1` first and then it will be updated according to rest of the configs.

#### Transfer and archive

Within the `project` map of a project's config, gitlabform processes `transfer_from` first. This gives additional flexibility.

```yaml
projects_and_groups:
  group_1/project_1:
    project:
      archive: true
      transfer_from: group_2/project_1
```

In the above example, the project will be transferred first and then it will be archived at the new location.

Also, Gitlab allows transferring a project or updating its path that is already archived. In the following example, if `group_2/project_1` is already archived, gitlabform will transfer the project to `group_1/foo-bar` and then unarchive it. Note that the project's path is changed from `project_1` to `foo-bar`.

```yaml
projects_and_groups:
  group_1/foo-bar:
    project:
      archive: false
      transfer_from: group_2/project_1
```
