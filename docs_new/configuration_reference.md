# Syntax Reference

The whole configuration for the app needs to be in a single YAML file of any name.

## Minimal example

Here is a minimal working configuration file example:
```yaml
config_version: 2

gitlab:
  url: https://gitlab.yourcompany.com
  # alternatively use the GITLAB_TOKEN environment variable
  token: "<private token of an admin user>"

groups_and_project:
  "*":
    project_settings:
      visibility: internal
```

## Mandatory keys

The configuration has to contain the following keys:
```yaml
# This key is required in configs for GitLabForm version 2.x.x
# This ensures that when the application behavior changes
# you won't apply unexpected configuration to your GitLab instance.
config_version: 2

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
```

## Optional keys

The configuration can, but doesn't have to contain the following keys:
```yaml
# this will skip these projects from being processed
skip_projects:
  - my-group/this-project-will-not-be-processed-with-gitlabform-when-running-for-my-group
  - my-group/and-this-too
  - my-group/everything-under/*

# this will skip these groups from being processed
skip_groups:
  - my-other-group
  - this-group-and-all-sub-groups/*
```

## Configuration levels

In GitLabForm you define the configuration for your groups and projects under `projects_and_groups:` key, on 3 levels:

| Name           | Key syntax      | Description                                                                                                                                                                                                                |
|----------------|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| common         | `"*"`           | the configuration that will be applied to all projects and all groups                                                                                                                                                      |
| group/subgroup | `group/*`       | the configuration that will be applied to everything under a given group/subgroup, recursively (so the group/subgroup itself, all the projects in it, all the subgroups in it and all the projects in the subgroups in it) |
| project        | `group/project` | the configuration for specific single projects                                                                                                                                                                             |

Each level is optional. Order does not matter.

Example:

```yaml
projects_and_groups:
  "*":
    # (...)

  group_1/*:
    # (...)
  group_1/project_1:
    # (...)
  group_1/project_2:
  # (...)
  group_1/project_3:
  # (...)

  group_2/*:
  # (...)
```

## Configuration sections

Under each of the keys described above, we put configuration to apply for given entities. These keys are called "sections" within this app.

Some configuration sections apply to **projects**, some to **groups**.

Syntax for each section is explained in detail on subpages - see links on the left.

## Effective configuration

To generate the effective configuration to apply for a given project or group, if it is configured on more than one level
(for example you run it for "group_1/my_project" with the example configuration above, where this project will
take configuration from all 3 levels), GitLabForm will **merge** those configurations.

Merging is **additive**, so for sections like `deploy_keys`, `secret_variables`, `hooks` on each lower level
the effective configuration will contain elements from higher levels plus elements from lower levels. Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      a_shared_key:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key # this name is show in GitLab
        can_push: false
  group_1/*:
    deploy_keys:
      another_key:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
        title: group_key # this name is show in GitLab
        can_push: false
```
For the above configuration, for a project `group_1/project_1` the effective configuration will contain 2 keys, `a_shared_key` and `another_key`.

## Skipping sections

If the only key under a section is `skip: true` then the given config section is not set AT ALL for a given entity. Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      a_shared_key:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key # this name is show in GitLab
        can_push: false
  group_1/*:
    deploy_keys:
      skip: true
```
For the above configuration, for a project `group_1/project_1` the effective configuration not manage the deploy keys at all.

## Breaking inheritance

You can prevent inheriting configuration from the higher levels by placing `inherit: false` under a given section. Example:
```yaml
projects_and_groups:
  "*":
    deploy_keys:
      a_shared_key:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL...
        title: global_key # this name is show in GitLab
        can_push: false
  group_1/*:
    deploy_keys:
      inherit: false
      another_key:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg...
        title: group_key # this name is show in GitLab
        can_push: false
```
For the above configuration, for a project `group_1/project_1` the effective configuration will contain only 1 key - the `another_key`.
