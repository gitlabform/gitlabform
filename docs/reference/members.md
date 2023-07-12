# Members

These sections are for managing the users and groups that are [members of a projects](https://docs.gitlab.com/ee/user/project/members/) and [groups](https://docs.gitlab.com/ee/user/group/#add-users-to-a-group).

## Project members

There are 4 keys that can be set in the `members` section:

* `groups` - to make other groups members of a given group. Here the key names are group paths and values are as described in the [share project with a group endpoint of the Projects API](https://docs.gitlab.com/ee/api/projects.html#share-project-with-group),
* `users` - to add single users. Here the key names are usernames and the values are as described in the [add member to a group or project endpoint of the Group and project members API](https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project),
* `enforce` - if set to `true` then this project will have ONLY the users and groups listed in the configuration as the *direct* members (so this setting will NOT affect the members inherited f.e. from a group that contains this project); default is `false`.
* `keep_bots` - if set to `true` then any existing project members that are bots will _not_ be removed regardless of the `enforce` setting; default is `false`.

Note: there has to be at least 1 user/group with "owner" access level per project - it's required by GitLab.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    members:
      groups:
        my-group:
          group_access: maintainer
        my-other-group/subgroup:
          group_access: maintainer
      users:
        my-user:
          access_level: maintainer
          expires_at: 2025-09-26
      enforce: true
      keep_bots: true
```

## Group members

There are 4 keys that can be set in the `group_members` section:

* `groups` - to make other groups members of a given group. Here the key names are group paths and values are as described in the [create a link to share a group with another group endpoint of the Groups API](https://docs.gitlab.com/ee/api/groups.html#create-a-link-to-share-a-group-with-another-group),
* `users` - to add single users. Here the key names are usernames and the values are as described in the [add member to a group or project endpoint of the Group and project members API](https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project),
* `enforce` - if set to `true` then removing a user or group from this config will also remove them from the group (so this setting will NOT affect the members inherited f.e. from a group that contains this group); default is `false`.
* `keep_bots` - if set to `true` then any existing group members that are bots will _not_ be removed regardless of the `enforce` setting; default is `false`.

Note: there has to be at least 1 user/group with "owner" access level per group - it's required by GitLab.

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_members:
      groups:
        another-group:
          group_access: no access
      users:
        my-user:
          access_level: owner
      enforce: true
      keep_bots: false
```
