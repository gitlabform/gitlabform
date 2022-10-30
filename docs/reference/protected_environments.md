# Protected environments

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

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
      env_1: # this is just a label
        name: env_1
        deploy_access_levels: &example_anchor_to_reuse_this_cfg
          - access_level: maintainer
          - user: johndoe
          - user_id: 1234
      env_2: # this is just a label
        name: env_2
        deploy_access_levels: *example_anchor_to_reuse_this_cfg
```
