# Tags protection

This section purpose is to protect and unprotect the project tags.

It works using the [Protected tags API](https://docs.gitlab.com/ee/api/protected_tags.html#protect-repository-tags) and its syntax is loosely based on it.

## Common features

The keys are the exact names of the tag or wildcards.

The values are:

* `protected`: `true` or `false`,
* (optional) `create_access_level`: minimal access levels allowed to create (default: `maintainer`, allowed: `no access`, `developer`, `maintainer`)

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    tags:
      "v*":
        protected: true
        create_access_level: developer
      "some-old-tag":
        protected: false
```

## Premium-only features

!!! info

    Below syntax and features require GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

In GitLab Premium instances you can also use the following extra keys under each branch:

* `allowed_to_create` key that can be set to the arrays containing any combination of:
    * `user` set to username,
    * `user_id` set to user id,
    * `group` set to group name (path),
    * `group_id` set to group id,
    * `access_level` set to [valid access level](https://docs.gitlab.com/ee/api/members.html#valid-access-levels)

Note that you should NOT use both `create_access_level` and `access_level` key under `allowed_to_create` - the result could be ambiguous, please choose the first or the second set.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    tags:
      # Allow specific users, groups, or roles to create this tag
      release-*:
        protected: true
        allowed_to_create:
          - user: jsmith # you can use usernames...
          - user: bdoe
          - group: another-group # ...or group names (paths)...
          - user_id: 15 # ...or user ids, if you know them...
          - group_id: 456 # ...or group ids, if you know them...
          - access_level: no access # do not allow creating tag by role (only specific user or group)
      alpha-release-by-devs-*:
        protected: true
        allowed_to_create:
          - access_level: developer
          - user: jsmith # you can use usernames...
          - user: 15
```
