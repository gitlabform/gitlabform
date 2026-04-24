# Protected branches

This section purpose is to manage the [protected branches](https://docs.gitlab.com/ee/user/project/protected_branches.html).

## Group-level protected branches

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

!!! warning

    Protected branch settings for groups are restricted to top-level groups only.

This section purpose is to manage the [group-level protected branches](https://docs.gitlab.com/ee/api/group_protected_branches.html).

Note: group protected branches only support access levels. Individual users and groups cannot be specified (this is a GitLab API limitation).

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_branches:
      main:
        protected: true
        push_access_level: no access
        merge_access_level: maintainer
      release/*:
        protected: true
        push_access_level: no access
        merge_access_level: maintainer
        unprotect_access_level: maintainer
```

## Project-level protected branches

### Community Edition vs Enterprise Edition
Note: that Gitlab Community Edition does not support setting `unprotect_access_level` and will always return `None` from the API, and there is also no way to manually set this through the UI.

### Functionality Differences
In Gitlab EE versions <=15.6.0 and Gitlab Community Edition, GitLabForm uses older functionality where to update Branch Protection rules, GitLabForm will remove protection and then re-protect the Branch using the new configuration.

- For EE: this is because the Update PATCH API was only added after 15.6.0
- For CE: this is because the Update PATCH API does nothing, nor throws an error, see: https://gitlab.com/rluna-gitlab/gitlab-ce/-/work_items/37

In later versions of Gitlab EE, GitLabForm will modify the Branch Protection rules in-place, see the [V4->V5 upgrade notes](../upgrade.md)

### Common features

The key names here may be:

* exact branch names,
* [branch names using wildcards](https://docs.gitlab.com/ee/user/project/protected_branches.html#configure-multiple-protected-branches-by-using-a-wildcard),

The values:

* have to contain a `protected` key set to `true` or `false`,
* if `protected: true`, then you can configure the protection using:
    * `push_access_level`, `merge_access_level`, `unprotect_access_level` keys, each set to one of the [valid access levels](https://docs.gitlab.com/ee/api/members.html#valid-access-levels) that will be the minimal access level required for a given action,
    * (optional) `allow_force_push` key set to `true` or `false`,

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    branches:
      # Keep this branch unprotected
      develop:
        protected: false
      # Allow merging by developers, but no direct commits
      main:
        protected: true
        push_access_level: no access
        merge_access_level: developer
        unprotect_access_level: maintainer
      # Disallow any changes to this branch
      special_protected_branch:
        protected: true
        push_access_level: no access
        merge_access_level: no access
        unprotect_access_level: maintainer
      # Protect branches with names matching wildcards
      '*-some-name-suffix':
        protected: true
        push_access_level: no access
        merge_access_level: developer
        unprotect_access_level: maintainer
      # Protect the branch but allow force pushes
      allow_to_force_push:
        protected: true
        push_access_level: no access
        merge_access_level: developer
        unprotect_access_level: maintainer
        allow_force_push: true
```

### Premium-only features

!!! info

    Below syntax and features require GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

In GitLab Premium instances you can also use the following extra keys under each branch:

* `code_owner_approval_required` set to `true` or `false`,
* `allowed_to_push`, `allowed_to_merge`, `allowed_to_unprotect` keys that can be set to the arrays containing any combination of:
    * `user` set to username,
    * `user_id` set to user id,
    * `group` set to group name (path),
    * `group_id` set to group id,
    * `access_level` set to [valid access level](https://docs.gitlab.com/ee/api/members.html#valid-access-levels)

Note that you should NOT use both `*_access_level` and `allowed_to_*` keys - the result could be ambiguous, please choose the first or the second set.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    branches:
      # Require code approvals, merge for developers, no direct commits
      extra:
        protected: true
        push_access_level: no access
        merge_access_level: developer
        unprotect_access_level: maintainer
        code_owner_approval_required: true
      # Allow specific users and groups to operate on this branch
      special:
        protected: true
        allowed_to_push:
          - user: jsmith # you can use usernames...
          - user: bdoe
          - group: another-group # ...or group names (paths)...
        allowed_to_merge:
          - user_id: 15 # ...or user ids, if you know them...
          - group_id: 456 # ...or group ids, if you know them...
        allowed_to_unprotect:
          - access_level: maintainer # ...or the whole access levels
```