# Protected environments

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

GitLabForm supports two ways to manage [protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html#protected-environments):

* **Group-level protected environments** (`group_protected_environments`) — Uses GitLab's [Group-level protected environments API](https://docs.gitlab.com/api/group_protected_environments/) to protect deployment tiers (`production`, `staging`, `testing`, `development`, or `other`) across a group and its descendant projects.
* **Project-level protected environments** (`protected_environments`) — Uses GitLab's [Protected environments API](https://docs.gitlab.com/api/protected_environments/) to protect named environments on individual projects.

## Group-level protected environments

This section purpose is to manage [group-level protected environments](https://docs.gitlab.com/api/group_protected_environments/).

Key names here are the deployment tier names (or any labels if you explicitly set `name:`), except if the key name is `enforce` and is set to `true` - then only the protected environments defined here will remain in the group, all others will be deleted. Setting `delete: true` on an entry unprotects that environment.

The supported values match the [protect a single environment endpoint of the Group-level protected environments API](https://docs.gitlab.com/api/group_protected_environments/#protect-a-single-environment), with the following conveniences:

* `user` with a username can be used instead of `user_id` with a user id (in `deploy_access_levels` and `approval_rules`),
* `group` with a group path can be used instead of `group_id` with a group id (in `deploy_access_levels` and `approval_rules`),
* `access_level` can have a string from the [valid access levels](https://docs.gitlab.com/api/group_protected_environments/#valid-access-levels) as a value instead of just a number.

!!! note

    GitLab requires any `group` / `group_id` specified in `deploy_access_levels` or `approval_rules` to be a subgroup under the target group, and any `user` / `user_id` to have at least the Maintainer role on that group. Because `group_1/*` configuration is inherited by subgroups in GitLabForm, add `skip: true` under `group_protected_environments` on subgroups if you only want the rule applied on the parent group.

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_protected_environments:
      enforce: true
      production:
        deploy_access_levels:
          - access_level: maintainer
            group_inheritance_type: 0
          - group: group_1/operators
        approval_rules:
          - group: group_1/approvers
            required_approvals: 2
      staging:
        deploy_access_levels:
          - access_level: developer
```

## Project-level protected environments

This section purpose is to manage the project [protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html#protected-environments).

Key names here are just any labels, except if the key name is `enforce` and is set to `true` - then only the protected environments defined here will remain in the project, all other will be deleted.

The supported values are like documented in the [protect environment endpoint of the Protected environments API](https://docs.gitlab.com/ee/api/protected_environments.html#protect-repository-environments), with the following changes:

* `user` with a username can be used instead of `user_id` with a user id,
* `group` with a group name can be used instead of `group_id` with a group id.
* `access_level` can have a string from the [valid access levels](https://docs.gitlab.com/ee/api/protected_environments.html#valid-access-levels) as a value instead of just a number,
* using `approval_rules` may work but this has not been tested yet,

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    protected_environments:
      enforce: true
      env_1: # name of the environment
        deploy_access_levels: &example_anchor_to_reuse_this_cfg
          - access_level: maintainer
          - user: johndoe
          - user_id: 1234
      env_2: # name of the environment
        deploy_access_levels: *example_anchor_to_reuse_this_cfg
```
