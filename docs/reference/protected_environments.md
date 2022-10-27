# Protected environments

This section purpose is to manage the [protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html#protected-environments).

!!! info

    Below syntax and features require GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's)

## Common features

The key names here may be:

* exact environment names

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    protected_environments:
      enforce: true # Removed entries will be modified to be unprotected 
      env_1:
        name: env_1
        deploy_access_levels: &example_anchor_to_reuse_this_cfg
          - access_level: 40
          - user: johndoe
          - user_id: 1234
      env_2:
        name: env_2
        deploy_access_levels: *example_anchor_to_reuse_this_cfg
```
