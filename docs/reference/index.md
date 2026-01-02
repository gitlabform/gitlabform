# Configuration reference

The whole configuration for the app needs to be in a single YAML file of any name. The default location used is the current working directory and the default name is `config.yml`.

## Minimal working config

Here is an example of a complete small config that actually does something:
```yaml
config_version: 3

gitlab:
  url: https://gitlab.yourcompany.com
  # alternatively use the GITLAB_TOKEN environment variable
  token: "<private token of an admin user>"

projects_and_groups:
  "*":
    project_settings:
      visibility: internal
```

## Mandatory top-level keys

The configuration has to contain the following top-level keys:
```yaml
# This key is required in configs for GitLabForm version 3.x.x
# This ensures that if the application behavior changes in a backward-incompatible way
# you won't apply unwanted configuration to your GitLab instance.
config_version: 3

# GitLab API access config
gitlab:
  # alternatively use the GITLAB_URL environment variable for this
  url: https://gitlab.yourcompany.com
  # alternatively use the GITLAB_TOKEN environment variable for this
  token: "<private token OR an OAuth2 access token of an admin user>"
  
  # ** optional parameters - below values are defaults **
  # whether the SSL certificate of your GitLab instance should be verified,
  # set this to `false` if you are using a self-signed certificate (not recommended)
  ssl_verify: true
  # timeout for the whole requests to the GitLab API, in seconds
  timeout: 10

  # ** advanced parameters **
  # Any additional parameters specified here will be passed to the python-gitlab library if they are supported. 
  # See https://python-gitlab.readthedocs.io/en/stable/api-usage.html#gitlab-client for available options.
  #
  # GitlabForm hasn't yet 100% migrated to use python-gitlab. Some processors are not using it and won't use these parameters.
  # For following migration to python-gitlab, see: https://github.com/gitlabform/gitlabform/issues/73
  #
  # REST API parameters (passed to python-gitlab's Gitlab client):
  # retry_transient_errors: false  # (defaults to `true`) retry requests that fail due to transient errors (5xx)
  #
  # GraphQL API parameters (passed to python-gitlab's GraphQL client):
  # max_retries: 10       # number of times to retry failed GraphQL requests
  # obey_rate_limit: true # automatically wait and retry if rate limit is hit

# Configuration to apply to GitLab projects, groups and subgroups
projects_and_groups:
  # (...)
  # See below.
```

## Projects and groups configuration

### Configuration hierarchy

In GitLabForm you define the configuration for your groups and projects under the `projects_and_groups:` top-level key, on 3 levels:

| Level name     | Key syntax                                                          | Description                                                                                                                                                                                                                |
|----------------|---------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| common         | `"*"`                                                               | the configuration that will be applied to all projects and all groups                                                                                                                                                      |
| group/subgroup | <nobr>`group/*`</nobr>, <nobr>`group/subgroup/*`</nobr>             | the configuration that will be applied to everything under a given group/subgroup, recursively (so the group/subgroup itself, all the projects in it, all the subgroups in it and all the projects in the subgroups in it) |
| project        | <nobr>`group/project`</nobr>, <nobr>`group/subgroup/project`</nobr> | the configuration for specific single projects                                                                                                                                                                             |

Each level is optional. Order does not matter.

Example:

```yaml
# (...) - other mandatory top-level keys

projects_and_groups:
  "*":
    # common-level config

  group_1/*:
    # group-level config
  group_1/project_1:
    # project-level config
  group_1/project_2:
    # project-level config
  group_1/project_3:
    # project-level config

  group_2/*:
    # group-level config
  group_2/project_1:
    # project-level config
  group_2/subgroup/*:
    # subgroup-level config
  group_2/subgroup/nested_project_1:
    # project-level config
```

### Configuration sections

Under each of the keys described above, we put configuration to apply for given entities. These keys are called "sections" within this app.

Some configuration sections apply only to **projects**, some to **groups**.

Syntax for each section is explained in detail on subpages - see links on the left.

### Effective configuration

To generate the effective configuration to apply for a given project or group, if it is configured on more than one level, GitLabForm will merge those configurations.


If under the exactly same keys there are different values in the more general (f.e. common) and more specific level (f.e. group level), then the more specific configuration will **overwrite** the more general one.

Example:
```yaml
projects_and_groups:
  # common settings for ALL projects in ALL groups
  "*":
    project_settings:
      default_branch: main
      visibility: internal

  group_1/*:
    project_settings:
      visibility: private # <-- different value!
``` 
With this configuration, for a project `group_1/project_1` the effective configuration will be like:
```yaml
project_settings:
  default_branch: main
  visibility: private
```

If there are more keys in the more specific config than in the more general one, then they are **added**. So for example for sections like `deploy_keys`, `variables`, `hooks` on each lower level the effective configuration will contain elements from the higher levels AND the elements from the lower levels.

Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      key_a:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key
        can_push: false
  
  group_1/*:
    deploy_keys:
      key_b: # <-- another key under deploy_keys!
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
        title: group_key
        can_push: false
```
With this configuration, for a project `group_1/project_1` the effective configuration will be:
```yaml
deploy_keys:
  key_a:
    key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
    title: global_key
    can_push: false
  key_b:
    key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
    title: group_key
    can_push: false
```

(What to do if you want have a key **removed**? You will need to use the "breaking inheritance" feature, explained in details below.)


**Warning**: dicts are additive but arrays are not! The more specific arrays are always overwriting the more general ones.

For example with this config:
```yaml
projects_and_groups:
  "*":
    merge_requests_approval_rules:
      default:
        approvals_required: 2
        name: "Team X or Y or super-user"
        groups:
          - group-x
          - group-y
        users:
          - super-user
  group_1/*:
    merge_requests_approval_rules:
      default:
        approvals_required: 1
        name: "Team Z"
        groups:
          - group-z
        users: []
```
With this configuration, for a project `group_1/project_1` the effective configuration will be:
```yaml
merge_requests_approval_rules:
  default:
    approvals_required: 1
    name: "Team Z"
    groups:
      - group-z
```
Note that the value of `groups` is an array, so the effective `groups` contains only the single element array from `group_1/*` - the arrays were not added!

Also note that the `users` is a key in the `default` dict, so we could not omit it. If we did that then __adding__ would work here and `users` would be effective set to `[super-user]`. We didn't want that and that's why we did set it an explicitly empty array `[]`.

### Breaking inheritance

You can prevent inheriting configuration from the higher levels by placing `inherit: false` under a given section.

Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      key_a:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key # this name is show in GitLab
        can_push: false
  group_1/*:
    deploy_keys:
      inherit: false
      key_b:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
        title: group_key # this name is show in GitLab
        can_push: false
```

For the above configuration, for a project `group_1/project_1`, the effective configuration for the section `deploy_keys` is like defined for the project `group_1/project_1` (specific configuration), with the more generic configuration in `"*"` being ignored (_More specific configuration will **overwrite** the more general one_).

In other words, it will be like this:

```yaml
deploy_keys:
  key_b:
    key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
    title: group_key # this name is show in GitLab
    can_push: false
```

!!! important

    `inherit: false` can be placed at ANY place in the configuration (if it makes sense).

### Skipping sections

If the only key under a section is `skip: true` then the given config section is not set AT ALL for a given entity.

Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      key_a:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key
        can_push: false
  group_1/*:
    deploy_keys:
      skip: true
```
For the above configuration, for a project `group_1/project_1` the deploy keys are not managed by GitLabForm all.

!!! important

    `skip: true` can be placed ONLY directly under a section name.

### Raw parameters passing

Some configuration sections, f.e. `project_settings`, will be directly send by the app via the API to specific GitLab API endpoints. This means that they key names and values are exactly like they are described in the appropriate API docs.

These sections are appropriately marked in the reference docs.

The advantages of this approach:

* you can use all the parameters from the API - for the `project_settings` it is over 40 parameters as of now (see [the GitLab API for Projects](https://docs.gitlab.com/ee/api/projects.html#edit-project)) while for `group_settings` - it is over 20 parameters (see [the GitLab API for Groups](https://docs.gitlab.com/ee/api/groups.html#update-group)),
* whenever GitLab adds a new feature to its API and you upgrade your GitLab instance, the feature is immediately configurable with GitLabForm, without updating this app,

The disadvantages:

* you have to read [the appropriate GitLab API docs](https://docs.gitlab.com/ee/api/api_resources.html) when you create your initial config for some entities, like Projects or Groups,
* if GitLab changes something in their API syntax, **you will have to apply the change in your config too** - there is no abstraction layer that will protect you from it.

## Optional top-level keys

The configuration can, but doesn't have to contain the following top-level keys:
```yaml
# list of projects that will not be processed
skip_projects:
  - my-group/this-project-will-not-be-processed-with-gitlabform
  - my-group/and-this-project0too
  - my-group/everything-under/*

# list of groups that will not be processed
skip_groups:
  - my-other-group
  - this-group-and-all-sub-groups/*
```
